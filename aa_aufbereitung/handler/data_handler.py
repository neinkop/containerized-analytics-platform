import pandas as pd # type: ignore
import pyarrow.parquet as pq # type: ignore
from sklearn.experimental import enable_iterative_imputer # type: ignore
from sklearn.impute import IterativeImputer # type: ignore
import holidays # type: ignore
import numpy as np # type: ignore
import random

class data_handler:

    def __init__(self, config, lh):
        self.config = config
        self.lh = lh
        self.dataframes = []
        self.raw_complete_df = None
        self.data_list = None
        self.files = []
        self.miced_df = None

    def load_data(self):
        self.data_list = open("/app/data/data.list", "r")
        test = self.config.getTestMode() # type: ignore
        test_rowgroups = self.config.getTestRowGroups() # type: ignore
        test_rows = self.config.getTestRows() # type: ignore
        
        for entry in self.data_list.readlines():
            path = entry.strip()
            try:
                open(path, "r").close()
            except FileNotFoundError:
                self.lh.error(f"Fehler: {path} Datei nicht gefunden. Bitte sicherstellen, dass die Datei im Verzeichnis /app/data/ vorhanden ist.")
                return
            if path.endswith(".csv"):
                self.lh.debug(f"Lade CSV chunkweise: {path}")
                chunks = []

                if test:
                    sample_size = 0.015  # 5% der Zeilen zufällig auswählen
                    for chunk in pd.read_csv(path,chunksize=100_000,dtype={"store_and_fwd_flag": "string"},skiprows=lambda i: i > 0 and random.random() > sample_size):
                        chunks.append(chunk)
                else:
                    for chunk in pd.read_csv(path,chunksize=100_000,dtype={"store_and_fwd_flag": "string"}):
                        chunks.append(chunk)
                # for chunk in pd.read_csv(path,chunksize=100_000,dtype={"store_and_fwd_flag": "string"}):
                #     if test:
                #         chunks.append(chunk.head(test_rows))
                #     else:
                #         chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            elif path.endswith(".parquet"):
                parquet_file = pq.ParquetFile(path)
                num_row_groups = parquet_file.num_row_groups
                if num_row_groups > test_rowgroups and test: num_row_groups = test_rowgroups
                self.lh.debug(f"Found {num_row_groups} row groups in {path}")
                dfs = []
                for i in range(num_row_groups):
                    df = parquet_file.read_row_group(i).to_pandas().copy()
                    if test: dfs.append(pd.DataFrame(df).head(test_rows))
                    else: dfs.append(df)           
                df = pd.concat(dfs, ignore_index=True)
            
            
            if "tpep_pickup_datetime" in df.columns:
                # Convert from epoch (ms) to a readable datetime string
                df["tpep_pickup_datetime"] = pd.to_datetime(
                    df["tpep_pickup_datetime"], unit="ms", errors="coerce"
                ).dt.strftime("%Y_%m_%d_%H_%M_%S")

                # Also convert dropoff timestamp to the same readable format
                if "tpep_dropoff_datetime" in df.columns:
                    df["tpep_dropoff_datetime"] = pd.to_datetime(
                        df["tpep_dropoff_datetime"], unit="ms", errors="coerce"
                    ).dt.strftime("%Y_%m_%d_%H_%M_%S")

                pickup_str = df["tpep_pickup_datetime"].astype(str)
            else:
                pickup_str = pd.Series(["" for _ in range(len(df))], index=df.index)
            
            if not "cbd_congestion_fee" in df.columns:
                df.insert(
                    len(df.columns),
                    "cbd_congestion_fee",
                    0
                )
            if not "forecast" in df.columns:
                df.insert(len(df.columns),"forecast","none")

            self.dataframes.append(df)

        df = pd.concat(self.dataframes, ignore_index=True)

        df.index = df.index.astype(str)
        df.index.name = "row_id"
        # Additional time-based features
        #df = self.raw_complete_df
        def cleanup(df):
            # 1. Remove negative or zero fares
            df = df[df['fare_amount'] > 0]

            # 2. Remove extreme fare outliers (above 99.5th percentile)
            fare_cap = df['fare_amount'].quantile(0.995)
            df = df[df['fare_amount'] <= fare_cap]

            # 3. Remove invalid trip distances
            df = df[(df['trip_distance'] > 0) & (df['trip_distance'] < 100)]

            # 4. Remove invalid passenger counts
            df = df[(df['passenger_count'] >= 1) & (df['passenger_count'] <= 6)]

            # 5. Remove rows with null coordinates
            #df = df.dropna(subset=['pickup_longitude', 'pickup_latitude', 'dropoff_longitude', 'dropoff_latitude'])
            # Wift auch KeyError

            # 6. Remove trips where pickup == dropoff coordinates (ghost trips)
            #df = df[~((df['pickup_longitude'] == df['dropoff_longitude']) & (df['pickup_latitude']  == df['dropoff_latitude']))]
            # Wirft ein KeyError
            return df
        
        def feature(df):
            col = "tpep_pickup_datetime"
            dt = pd.to_datetime(df[col], format="%Y_%m_%d_%H_%M_%S")
            df["weekday"] = dt.dt.dayofweek
            df["is_weekend"] = dt.dt.dayofweek.isin([5, 6]).astype(int)

            df["season"] = dt.dt.month.map({12:0,1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:3,10:3,11:3})
            
            import holidays # type: ignore
            print(df["tpep_pickup_datetime"].str[:4].astype(int).unique())
            #dt.dt.year
            dates = [d for d, _ in holidays.US(years=df["tpep_pickup_datetime"].str[:4].astype(int).unique()).items()]
            df["is_holiday"] = dt.dt.date.isin(dates).astype(int)
            

            df["is_school_holiday"] = 0
            #(df["tpep_pickup_datetime"] - pd.Timedelta(days=1)).dt.date.isin(dates).astype(int)
            df["before_holiday"] = (dt - pd.Timedelta(days=-1)).dt.date.isin(dates).astype(int)
            df["after_holiday"] = (dt - pd.Timedelta(days=1)).dt.date.isin(dates).astype(int)

            df["is_rush_hour"] = dt.dt.hour.isin([7,8,9,16,17,18]).astype(int)
            df["is_event"] = 0
            df["dow_sin"] = np.sin(2 * np.pi * dt.dt.dayofweek / 7)
            df["dow_cos"] = np.cos(2 * np.pi * dt.dt.dayofweek / 7)
            df["month_sin"] = np.sin(2 * np.pi * dt.dt.month / 12)
            df["month_cos"] = np.cos(2 * np.pi * dt.dt.month / 12)
            return df
        #self.raw_complete_df = 
        cleanup(df)
        #self.raw_complete_df = 
        feature(df)
        

        for col, prefix in [ ("tpep_pickup_datetime", "pickup"), ("tpep_dropoff_datetime", "dropoff")]:
            df[f"{prefix}_year"] = pd.to_datetime(df[col], format="%Y_%m_%d_%H_%M_%S").dt.year
            df[f"{prefix}_month"] = pd.to_datetime(df[col], format="%Y_%m_%d_%H_%M_%S").dt.month
            df[f"{prefix}_day"] = pd.to_datetime(df[col], format="%Y_%m_%d_%H_%M_%S").dt.day
            df[f"{prefix}_hour"] = pd.to_datetime(df[col], format="%Y_%m_%d_%H_%M_%S").dt.hour

        #df.set_index("row_id", inplace=True)
        print(df.head(2).to_json(orient="index"))
        self.raw_complete_df = df

    def getCompleteRawDataframe(self):
        return self.raw_complete_df
    
    def miceTipAmounts(self):
        """
        Soll das Trinkgeld (tip_amount) vorhersagen und imputieren für Taxifahrten die Bar bezahlt wurden (payment_type = 2). 
        --> Tip wird nur bei Kartenzahlung erhoben, daher ist das Trinkgeld bei Barzahlung immer 0.0

        Als Methode hierfür soll MICE (Multiple Imputation by Chained Equations) verwendet werden.
        Die Grundlage hierfür soll der Betrag sein, der für die Fahrt bezahlt wurde (total_amount).

        Abschließend soll ein vollständiger Dataframe mit den imputierten Werten zurückgegeben werden.
        """
        df = self.raw_complete_df.copy()
        
        # Relevante Spalten für MICE
        mice_cols = ['total_amount', 'fare_amount', 'trip_distance', 'tip_amount']
        mice_data = df[mice_cols].copy()

        # Tip bei Barzahlung als fehlend markieren
        mice_data.loc[df['payment_type'] == 2, 'tip_amount'] = pd.NA

        # MICE Imputer
        imputer = IterativeImputer(random_state=42,max_iter=10)

        # Imputation durchführen
        imputed_array = imputer.fit_transform(mice_data)

        # Zurück in DataFrame
        imputed_df = pd.DataFrame(imputed_array, columns=mice_cols)

        # Nur positive Imputationswerte (Tipps können nicht negativ sein)
        imputed_df['tip_amount'] = imputed_df['tip_amount'].clip(lower=0)

        # Nur tip_amount zurückschreiben
        df['tip_amount'] = imputed_df['tip_amount'].values
        self.miced_df = df
        return self.miced_df
    
    def getMicedDataframe(self):
        return self.miced_df
            
    def getFiles(self):
        return self.files