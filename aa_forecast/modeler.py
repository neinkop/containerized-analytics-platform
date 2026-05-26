import pandas as pd # type: ignore
import statsmodels.api as sm  # type: ignore
import statsmodels.formula.api as smf # type: ignore
import numpy as np # type: ignore
import holidays # type: ignore

class modeler:
    def __init__(self, lh, df):
        self.lh = lh
        self.df = df

    def __get_valid_families(self, target_series, method):
        families = {}

        # COUNT → count models
        if method == "count":
            families["poisson"] = sm.families.Poisson()

            # Optional: Negative Binomial for overdispersion
            families["negbin"] = sm.families.NegativeBinomial(alpha=1.0)

            return families

        # MEAN / continuous → regression models
        families["gaussian"] = sm.families.Gaussian()

        # Only for strictly positive data
        if (target_series > 0).all():
            families["gamma"] = sm.families.Gamma()
            families["inverse_gaussian"] = sm.families.InverseGaussian()

        return families

    def handle(self, year, month, day, filter):
        method = filter.getAggregationMethod()
        dimensions = filter.getAggregationColumns()
        dimensions_org = dimensions.copy()
        #print("Dimensions before processing:", dimensions)
        target = filter.getColumns()[-1]
        #print(dimensions)
        forecast = False
        if "forecast" in dimensions:
            dimensions.remove("forecast")
            forecast = True
        if len(dimensions) == 0 and (not month or not day):
            self.lh.debug("Request with Invalid filter parameters - Status 400 (modeler)")
            return ("Invalid filter parameters", 400)
        
        #print(dimensions)
        
        df = self.df.copy()
        
        # Original
        #if day: dimensions = ["weekday", "is_weekend", "is_holiday", "is_school_holiday", "before_holiday", "after_holiday", "is_event", "dow_sin", "dow_cos"] + dimensions
        #if month: dimensions = ["season", "month_sin", "month_cos"] + dimensions

        # Angepasst
        dimensions_day = ["is_weekend", "is_holiday", "is_school_holiday", "before_holiday", "after_holiday", "is_event", "dow_sin", "dow_cos"]
        for dim in dimensions:
            if dim in dimensions_day:
                dimensions.remove(dim)
        if day: dimensions = ["is_weekend", "is_holiday", "is_school_holiday", "before_holiday", "after_holiday", "is_event", "dow_sin", "dow_cos"] + dimensions
        if month: dimensions = ["month_sin", "month_cos"] + dimensions

        if ("pickup_hour" in dimensions) or ("dropoff_hour" in dimensions): dimensions.append("is_rush_hour") 
        print(f"Final dimensions for modeling: {dimensions}")
        #if target in dimensions: dimensions = dimensions.remove(target)
        self.lh.debug(f"Anfrage - Method: {method}, Dimensions: {dimensions}, Target: {target} (year: {year}, month: {month}, day: {day})")
        df_agg = (
            df.groupby(dimensions)
            .agg(**{target: (target, method)})
            .reset_index()
        )
        df_agg = df_agg.replace([np.inf, -np.inf], np.nan).dropna()

        # Normalisierung für count: Trainingsdaten umfassen mehrere Jahre/Monate,
        # der groupby kumuliert alle Perioden → durch Anzahl relevanter Perioden teilen,
        # damit die Vorhersage mit einem einzelnen Jahr/Monat vergleichbar ist.
        if method == "count":
            if day and month:
                # Tag-Ebene: wie viele Jahre haben Daten für genau diesen Monat+Tag?
                n_periods = (
                    df[
                        (df["pickup_month"] == int(month)) &
                        (df["pickup_day"]   == int(day))
                    ]["pickup_year"].nunique()
                    if "pickup_month" in df.columns and "pickup_day" in df.columns
                    else 1
                )
            elif month:
                # Monats-Ebene: wie viele Jahre haben Daten für diesen Monat?
                n_periods = (
                    df[df["pickup_month"] == int(month)]["pickup_year"].nunique()
                    if "pickup_month" in df.columns
                    else 1
                )
            else:
                # Jahres-Ebene: wie viele Jahre im Trainingsdatensatz?
                n_periods = (
                    df["pickup_year"].nunique()
                    if "pickup_year" in df.columns
                    else 1
                )
            if n_periods > 1:
                self.lh.debug(f"Count-Normalisierung: ÷ {n_periods} Zeitperioden")
                df_agg[target] = df_agg[target] / n_periods

        # Log-Transformation only for mean (continuous targets)
        use_log = False
        if method == "mean":
            df_agg[target] = np.log1p(df_agg[target])
            use_log = True
        
        ## Formel generieren
        dimensions_uncat = dimensions.copy()
        for i in range(len(dimensions)):
            if dimensions[i][len(dimensions[i])-3:] not in ["cos", "sin"]:
                dimensions[i] = f"C({dimensions[i]})"

        formel = target + " ~ " + " + ".join(dimensions)
        #print(f"Formel: {formel}")
        
        families = self.__get_valid_families(df_agg[target], method)
        pred = self.predict(df_agg, formel, target, self.__gen_pred_df(dimensions_uncat, target, year, month, day, df_agg), families, dimensions_org, use_log, forecast)

        self.lh.debug(f"Anfrage - Method: {method}, Dimensions: {dimensions}, Target: {target} (year: {year}, month: {month}, day: {day}) - predicted with {len(families)} families and row count of pred_df: {len(pred)}")
        return pred

    def predict(self, df_agg, formula, target, pred_df, families, dimensions_org, use_log=False, forecast=False):
        dfs = []
        model_summaries = []

        # GLM Modelle
        for name, family in families.items():
            current_pred_df = pred_df.copy()
            try:
                model = smf.glm(formula=formula, data=df_agg, family=family).fit()
                preds = model.predict(current_pred_df)

                # Predictions
                pred_out = current_pred_df.copy()
                if use_log:
                    pred_out[target] = np.expm1(preds)
                else:
                    pred_out[target] = preds
                if forecast:
                    pred_out["forecast"] = name
                pred_out["model"] = name
                dfs.append(pred_out)

                # Summary
                for param, value in model.params.items():
                    model_summaries.append({
                        "model": name,
                        "parameter": param,
                        "coef": value,
                        "pvalue": model.pvalues.get(param),
                        "aic": model.aic,
                        "nobs": int(model.nobs)
                    })
                #print(model.summary())

            except Exception as e:
                print(f"[WARNING] Model {name} failed: {e}")

        # OLS Modell
        current_pred_df = pred_df.copy()
        ols_model = smf.ols(formula=formula, data=df_agg).fit()
        preds = ols_model.predict(current_pred_df)

        pred_out = current_pred_df.copy()
        if use_log:
            pred_out[target] = np.expm1(preds)
        else:
            pred_out[target] = preds
        if forecast:
            pred_out["forecast"] = "linear_regression"
        pred_out["model"] = "linear_regression"
        dfs.append(pred_out)

        # OLS Summary
        for param, value in ols_model.params.items():
            model_summaries.append({
                "model": "linear_regression",
                "parameter": param,
                "coef": value,
                "pvalue": ols_model.pvalues.get(param),
                "aic": ols_model.aic,
                "nobs": int(ols_model.nobs),
                "rsquared": ols_model.rsquared,
                "rsquared_adj": ols_model.rsquared_adj
            })

        result_df = pd.concat(dfs)
        summary_df = pd.DataFrame(model_summaries)

        # Nur originale Dimensionen behalten
        cols_to_keep = dimensions_org.copy()
        if forecast and "forecast" not in cols_to_keep:
            cols_to_keep.append("forecast")
        cols_to_keep.append(target)
        cols_to_keep.append("model")

        cols_to_keep = [c for c in cols_to_keep if c in result_df.columns]
        result_df = result_df[cols_to_keep]

        return {
            "predictions": result_df.to_dict(orient="records"),
            "model_summary": summary_df.to_dict(orient="records")
        }

    def __gen_pred_df(self, dimensions, target, year, month, day, df_agg):
        from itertools import product

        dummy_lists = self.create_dummy_lists(dimensions, year, month, day, df_agg)
        

        keys = list(dummy_lists.keys())
        values = list(dummy_lists.values())

        combinations = list(product(*values))

        df = pd.DataFrame(combinations, columns=keys)
        #df = pd.DataFrame()
        if month:
            df["month_sin"] = np.sin(2 * np.pi * int(month) / 12)
            df["month_cos"] = np.cos(2 * np.pi * int(month) / 12)
            df["season"] = self.getSeason(int(month))
        if day:
            import datetime
            date = datetime.datetime.strptime(f"{year}-{month:02}-{day:02}", '%Y-%m-%d').date()
            dayofweek = date.weekday()
            df["dow_sin"] = np.sin(2 * np.pi * int(dayofweek) / 7)
            df["dow_cos"] = np.cos(2 * np.pi * int(dayofweek) / 7)
            df["weekday"] = int(dayofweek)
            #["", "", "", "", "", "is_event",
            df["is_weekend"] = int(dayofweek in [5, 6])
            #try:
            import holidays # type: ignore
            dates = [d for d, _ in holidays.US(years=[date.year]).items()]
            is_holiday = 1
            if date in dates: is_holiday = 1
            else: is_holiday = 0
            df["is_holiday"] = is_holiday
            df["is_school_holiday"] = 0
            df["before_holiday"] = df["is_holiday"].shift(-1).fillna(0).astype(int)
            df["after_holiday"] = df["is_holiday"].shift(1).fillna(0).astype(int)
            df["is_event"] = 0
            if "pickup_hour" in dimensions or "dropoff_hour" in dimensions:
                print("Generating rush hour feature for prediction dataframe...")
                if "pickup_hour" in df.columns:
                    df["is_rush_hour"] = df["pickup_hour"].isin([7,8,9,16,17,18]).astype(int)
                elif "dropoff_hour" in df.columns:
                    df["is_rush_hour"] = df["dropoff_hour"].isin([7,8,9,16,17,18]).astype(int)
        

        # 🔥 Fallback: ensure column exists for patsy formula
        if "is_rush_hour" not in df.columns:
            df["is_rush_hour"] = 0
        return df
    
    def getSeason(self, month):
        """Helper function to determine season based on month. Because map is not working for some reason."""
        if month in [12, 1, 2]:
            return 0
        elif month in [3, 4, 5]:
            return 1
        elif month in [6, 7, 8]:
            return 2
        elif month in [9, 10, 11]:
            return 3
        return 0
    
    def create_dummy_lists(self, attr, year=None, month=None, day=None, df_agg=None):
        dummy_data = {}

        if "VendorID" in attr and "VendorID" in self.df.columns:
            dummy_data["VendorID"] = list(df_agg["VendorID"].dropna().unique())

        if "payment_type" in attr and "payment_type" in self.df.columns:
            dummy_data["payment_type"] = list(df_agg["payment_type"].dropna().unique())

        if "RatecodeID" in attr and "RatecodeID" in self.df.columns:
            dummy_data["RatecodeID"] = list(df_agg["RatecodeID"].dropna().unique())

        if "store_and_fwd_flag" in attr and "store_and_fwd_flag" in self.df.columns:
            dummy_data["store_and_fwd_flag"] = list(df_agg["store_and_fwd_flag"].dropna().unique())

        if "weekday" in attr:
            if day and month and year:
                import datetime
                date = datetime.datetime.strptime(f"{year}-{int(month):02}-{int(day):02}", '%Y-%m-%d').date()
                dummy_data["weekday"] = [date.weekday()]
            else:
                dummy_data["weekday"] = list(range(0, 7))

        if "pickup_year" in attr:
            dummy_data["pickup_year"] = [2026]

        if "pickup_month" in attr:
            if (year and not month):
                dummy_data["pickup_month"] = list(range(1, 13))
            else:
                dummy_data["pickup_month"] = [int(month)]

        if "pickup_day" in attr:
            if (year and month and not day):
                dummy_data["pickup_day"] = list(range(1, 32))
            else:
                dummy_data["pickup_day"] = [int(day)]                

        if "pickup_hour" in attr:
            dummy_data["pickup_hour"] = list(range(0, 24))

        if "dropoff_year" in attr:
            dummy_data["dropoff_year"] = [2026]

        if "dropoff_month" in attr:
            dummy_data["dropoff_month"] = list(range(1, 13))

        if "dropoff_day" in attr:
            dummy_data["dropoff_day"] = list(range(1, 32))

        if "dropoff_hour" in attr:
            dummy_data["dropoff_hour"] = list(range(0, 24))

        return dummy_data