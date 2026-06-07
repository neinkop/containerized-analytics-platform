"""
python3 -m venv venv
source venv/bin/activate
python3 -m pip install streamlit
python3 -m pip install requests
python3 -m pip install pandas
python3 -m pip install plotly
"""
import streamlit as st # type: ignore
import pandas as pd # type: ignore
import requests # type: ignore
import plotly.express as px # type: ignore

# ============================================
# CONFIG
# ============================================
API_CONFIGS = {
    "aa_api_default": {
        "base_url": "http://aa_api:8090/data",
        "summary_url": "http://aa_api:8090/data_summary",
        "default": True
    },
    "aa_api_forecast": {
        "base_url": "http://aa_forecast:8080/data",
        "summary_url": "http://aa_forecast:8080/data_summary",
        "default": False
    }
}
forecast_apis = [
    api_name
    for api_name, cfg in API_CONFIGS.items()
    if not cfg.get("default", False)
]
def build_url(year, month=None, day=None):
    if month is None:
        return f"{BASE_URL}/{year}/" # type: ignore
    
    month_str = f"{month:02d}"

    if day is None:
        return f"{BASE_URL}/{year}/{month_str}/" # type: ignore
    
    day_str = f"{day:02d}"
    return f"{BASE_URL}/{year}/{month_str}/{day_str}" # type: ignore

# ============================================
# SUMMARY DATA FETCH
# ============================================
def fetch_available_dates(summary_url):
    try:
        res = requests.get(summary_url, timeout=5)

        if res.status_code == 200:
            data = res.json()

            # Basisvalidierung
            if not isinstance(data, dict):
                st.warning(f"⚠️ Ungültige Antwort von {summary_url}")
                return None

            return data
        else:
            st.warning(f"⚠️ API nicht erreichbar: {summary_url}")
            return None

    except Exception:
        st.warning(f"⚠️ API nicht erreichbar: {summary_url}")
        return None
# ============================================
# MAPPINGS
# ============================================
payment_map = {
    0: "Flex Fare",
    1: "Credit Card",
    2: "Cash",
    3: "No Charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided"
}

vendor_map = {
    1: "Creative Mobile",
    2: "Curb",
    6: "Myle",
    7: "Helix"
}

ratecode_map = {
    1: "Standard",
    2: "JFK",
    3: "Newark",
    4: "Nassau/Westchester",
    5: "Negotiated",
    6: "Group Ride",
    99: "Unknown"
}

weekday_map = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag"
}

# ============================================
# API LOGIK (SMART)
# ============================================
@st.cache_data
def fetch_data(base_url, years, months, days, dimensions, metric, aggregation):
    all_data = []

    for year in years:

        # Filter passende Monate und Tage
        selected_months = [m for m in months if m.startswith(year)]
        selected_days = [d for d in days if d.startswith(year)]

        # Jahre ohne passende Auswahl überspringen
        # Wenn Tage gewählt → nur Jahre mit passenden Tagen berücksichtigen
        if days and not selected_days:
            continue

        # Wenn keine Tage, aber Monate gewählt → nur passende Monate berücksichtigen
        if not days and months and not selected_months:
            continue

        # PRIORITÄT:
        # 1. Tage
        # 2. Monate
        # 3. Jahr

        # Fall 1: Tage (höchste Priorität)
        if selected_days:
            for day_str in selected_days:
                y, m, d = day_str.split("-")

                url = f"{base_url}/{y}/{m}/{d}"

                filter_vars = dimensions + [metric]
                params = {"filter": ",".join(filter_vars)}
                if aggregation:
                    params["aggr"] = f"{aggregation}," + ",".join(dimensions)

                res = requests.get(url, params=params)

                if res.status_code == 200:
                    data = res.json()

                    if isinstance(data, dict) and "predictions" in data:
                        df = pd.DataFrame(data["predictions"])
                        df["_model_summary"] = [data.get("model_summary", [])] * len(df)
                    else:
                        df = pd.DataFrame(data)

                    df = df.reset_index()
                    df["year"] = int(y)
                    df["month"] = int(m)
                    df["day"] = int(d)
                    all_data.append(df)
                else:
                    st.write("REQUEST URL:", url, "| API:", base_url ,"| Status-Code:", res.status_code)
                    st.write(res.content, params)

        # Fall 2: Monate
        elif selected_months:
            for month_str in selected_months:
                y, m = month_str.split("-")

                url = f"{base_url}/{y}/{m}/"

                filter_vars = dimensions + [metric]
                params = {"filter": ",".join(filter_vars)}
                if aggregation:
                    params["aggr"] = f"{aggregation}," + ",".join(dimensions)

                res = requests.get(url, params=params)

                if res.status_code == 200:
                    data = res.json()

                    if isinstance(data, dict) and "predictions" in data:
                        df = pd.DataFrame(data["predictions"])
                        df["_model_summary"] = [data.get("model_summary", [])] * len(df)
                    else:
                        df = pd.DataFrame(data)

                    df = df.reset_index()
                    df["year"] = int(y)
                    df["month"] = int(m)
                    all_data.append(df)
                else:
                    st.write("REQUEST URL:", url, "| API:", base_url ,"| Status-Code:", res.status_code)
                    st.write(res.content, params)

        # Fall 3: nur Jahr
        else:
            url = f"{base_url}/{year}/"

            filter_vars = dimensions + [metric]
            params = {"filter": ",".join(filter_vars)}
            if aggregation:
                params["aggr"] = f"{aggregation}," + ",".join(dimensions)

            res = requests.get(url, params=params)

            if res.status_code == 200:
                data = res.json()

                if isinstance(data, dict) and "predictions" in data:
                    df = pd.DataFrame(data["predictions"])
                    df["_model_summary"] = [data.get("model_summary", [])] * len(df)
                else:
                    df = pd.DataFrame(data)

                df = df.reset_index()
                df["year"] = year
                all_data.append(df)
            else:
                st.write("REQUEST URL:", url, "| API:", base_url ,"| Status-Code:", res.status_code)
                st.write(res.content, params)

    if not all_data:
        return pd.DataFrame(), []

    df = pd.concat(all_data, ignore_index=True)

    # Modellzusammenfassungen sammeln (falls vorhanden)
    model_summaries = []
    if "_model_summary" in df.columns:
        for entry in df["_model_summary"].dropna():
            if isinstance(entry, list):
                model_summaries.extend(entry)
        df = df.drop(columns=["_model_summary"])
    else:
        model_summaries = []

    # Nur aggregieren, wenn ausgewählt
    if aggregation:
        group_cols = dimensions.copy()

        if "year" in df.columns:
            group_cols.append("year")
        if "month" in df.columns:
            group_cols.append("month")
        if "day" in df.columns:
            group_cols.append("day")

        if aggregation == "sum":
            df = df.groupby(group_cols)[metric].sum().reset_index()
        elif aggregation == "mean":
            df = df.groupby(group_cols)[metric].mean().reset_index()
        elif aggregation == "count":
            # API liefert bereits aggregierte Counts (z.B. fare_amount = Anzahl)
            # Daher NICHT erneut count() anwenden (würde immer 1 ergeben),
            # sondern aufsummieren, falls mehrere Quellen kombiniert werden
            df = df.groupby(group_cols)[metric].sum().reset_index()

    return df, model_summaries

# ============================================
# UI
# ============================================
st.set_page_config(layout="wide")
st.title("Dashboard")


st.sidebar.header("Einstellungen")
# Alle APIs neu laden
if st.sidebar.button("🔄 Daten neu laden"):
    st.cache_data.clear()
    st.rerun()

selected_apis = st.sidebar.multiselect(
    "APIs auswählen",
    list(API_CONFIGS.keys()),
    key="selected_apis",
    placeholder="Option auswählen"
)
if not selected_apis:
    selected_apis = list(API_CONFIGS.keys())

summary_data_all = {"years": set(), "months": set(), "days": set()}
# Neue Liste für erreichbare APIs
reachable_apis = []
# Immer ALLE APIs für verfügbare Zeiträume abfragen (unabhängig von Auswahl)
for api, cfg in API_CONFIGS.items():
    data = fetch_available_dates(cfg["summary_url"])
    if data is None:
        continue
    summary_data_all["years"].update(data.get("years", []))
    summary_data_all["months"].update(data.get("months", []))
    summary_data_all["days"].update(data.get("days", []))
    reachable_apis.append(api)

# Nach der Schleife: Auswahl auf erreichbare APIs beschränken
selected_apis = [api for api in selected_apis if api in reachable_apis]

summary_data = {
    "years": sorted(summary_data_all["years"]),
    "months": sorted(summary_data_all["months"]),
    "days": sorted(summary_data_all["days"]),
}

available_years = sorted([str(y) for y in summary_data.get("years", [])])
years = st.sidebar.multiselect(
    "Jahre",
    available_years,
    key="years",
    placeholder="Option auswählen"
)

# Monate dynamisch (abhängig von Jahren)
available_months = [
    str(m) for m in summary_data.get("months", [])
    if str(m).split("-")[0] in [str(y) for y in years]
]
months = st.sidebar.multiselect(
    "Monate",
    available_months,
    key="months",
    placeholder="Option auswählen"
)

# Tage dynamisch (abhängig von Monaten)
available_days = [
    str(d) for d in summary_data.get("days", [])
    if str(d)[:7] in [str(m) for m in months]
]
days = st.sidebar.multiselect(
    "Tage",
    available_days,
    key="days",
    placeholder="Option auswählen"
)

metrics = st.sidebar.multiselect(
    "Kennzahlen",
    [
        "total_amount",
        "fare_amount",
        "trip_distance",
        "tip_amount",
        "passenger_count",
        "tolls_amount",
        "congestion_surcharge"
    ],
    key="metrics",
    placeholder="Option auswählen"
)

aggregation = st.sidebar.selectbox(
    "Aggregation",
    ["sum", "mean", "count"],
    index=None,
    placeholder="Option auswählen"
)
dimensions = st.sidebar.multiselect(
    "Gruppierung",
    [
        "forecast",
        "VendorID",
        "payment_type",
        "RatecodeID",
        "PULocationID",
        "DOLocationID",
        "store_and_fwd_flag",
        "pickup_year","pickup_month","pickup_day","pickup_hour",
        "dropoff_year","dropoff_month","dropoff_day","dropoff_hour",
        "is_weekend","season","is_holiday","is_school_holiday","before_holiday","after_holiday","is_rush_hour","is_event", "weekday"
        
    ],
    placeholder="Option auswählen"
)

# Default-API Validierung und Reihenfolge
default_apis = [k for k, v in API_CONFIGS.items() if v.get("default")]
if len(default_apis) != 1:
    st.error("❌ Es muss genau eine Default-API geben")
    st.stop()

default_api = default_apis[0]

# Reihenfolge: bei forecast zuerst Nicht-Default
if "forecast" in dimensions:
    selected_apis = sorted(
        selected_apis,
        key=lambda x: x == default_api
    )

chart_type = st.sidebar.selectbox(
    "Diagrammtyp",
    [
        "Line (Zeitdimension)",
        "Bar (1 & 2 Dimension)",
        "Heatmap (2 Dimensionen)",
        "Scatter (2 Dimensionen)",
        "3D Scatter (2 Dimensionen + Kennzahl)"
    ]
)

output_mode = st.sidebar.multiselect(
    "Anzeige",
    ["Tabelle", "Visualisierung"],
    key="output_mode",
    placeholder="Option auswählen"
)
if not output_mode:
    output_mode = ["Visualisierung", "Tabelle"]

 # ============================================
# VALIDIERUNG AUSWAHL
# ============================================
if (not years and not months and not days) or not metrics:
    st.info("ℹ️ Bitte wählen Sie mindestens einen Zeitraum und eine Kennzahl aus.")
    st.stop()

# ============================================
# DATEN LADEN
# ============================================


if (aggregation and not dimensions):
    st.sidebar.error("⚠️ Bitte Gruppierung auswählen")
    st.stop()

if (dimensions and not aggregation):
    st.sidebar.error("⚠️ Bitte Aggregation auswählen")
    st.stop()

dfs = {}



for metric in metrics:
    all_api_dfs = []

    for api in selected_apis:
        if api in forecast_apis and len(dimensions) == 1 and (years and months and not days):
            st.warning(f"⚠️ API '{api}' unterstützt keine monatliche Aggregation mit nur einer Dimension. Bitte wählen Sie mehr Dimensionen oder einen Tag aus.")
        else:
            print(api)
            cfg = API_CONFIGS[api]
            #st.write("CALLING API:", api)
            try:
                df_api, model_summary = fetch_data(cfg["base_url"], years, months, days, dimensions, metric, aggregation)
            except Exception:
                st.warning(f"⚠️ API nicht erreichbar: {cfg['base_url']}")
                continue
            if not df_api.empty:
                if model_summary:
                    if "all_model_summaries" not in locals():
                        all_model_summaries = []
                    all_model_summaries.extend(model_summary)
                df_api["source_api"] = api
                all_api_dfs.append(df_api)

    if all_api_dfs:
        df_all = pd.concat(all_api_dfs, ignore_index=True)

        # forecast Kennzeichnung (nur wenn nicht vorhanden)
        if "forecast" not in df_all.columns:
            df_all["forecast"] = df_all["source_api"].apply(
                lambda x: 0 if x == default_api else 1
            )
        else:
            # vorhandenen Wert behalten, optional API Info ergänzen
            df_all["forecast_api"] = df_all["source_api"]

        # Duplikate nach Datum + Dimensionen behandeln
        time_cols = [c for c in ["year", "month", "day"] if c in df_all.columns]
        group_cols = dimensions.copy()

        for col in time_cols:
            if col not in group_cols:
                group_cols.append(col)

        # source_api nicht Teil der Gruppierung
        group_cols = [c for c in group_cols if c != "source_api"]

        # Default priorisieren
        df_all = df_all.sort_values(by=["forecast"])

        df_all = df_all.drop_duplicates(subset=group_cols, keep="first")

        dfs[metric] = df_all
    else:
        dfs[metric] = pd.DataFrame()

if not dfs:
    st.error("❌ Keine Daten gefunden")
    st.stop()

for metric, df in dfs.items():

    if df.empty:
        continue

    st.subheader(f"Kennzahl: {metric}")

    if "payment_type" in df.columns:
        df["payment_type"] = (
            pd.to_numeric(df["payment_type"], errors="coerce")
            .map(payment_map)
            .fillna(df["payment_type"])
        )

    if "VendorID" in df.columns:
        df["VendorID"] = (
            pd.to_numeric(df["VendorID"], errors="coerce")
            .map(vendor_map)
            .fillna(df["VendorID"])
        )

    if "RatecodeID" in df.columns:
        df["RatecodeID"] = (
            pd.to_numeric(df["RatecodeID"], errors="coerce")
            .map(ratecode_map)
            .fillna(df["RatecodeID"])
        )

    if "weekday" in df.columns:
        df["weekday"] = (
            pd.to_numeric(df["weekday"], errors="coerce")
            .map(weekday_map)
            .fillna(df["weekday"])
        )

    # ============================================
    # DYNAMISCHE FILTER (pro Dimension)
    # ============================================
    if dimensions:
        with st.expander("Filter"):
            for dim in dimensions:
                if dim in df.columns:
                    values = sorted(df[dim].dropna().unique())
                    selected = st.multiselect(
                        f"{dim} auswählen",
                        values,
                        default=values,
                        key=f"{metric}_{dim}"
                    )
                    df = df[df[dim].isin(selected)]

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Summe", f"{df[metric].sum():.2f}")
    col2.metric("Ø", f"{df[metric].mean():.2f}")
    col3.metric("Anz. Datensätze", len(df))

    # Visualisierung
    if "Visualisierung" in output_mode:
        st.subheader("Visualisierung")

        if chart_type.startswith("Bar") and len(dimensions) == 1:
            fig = px.bar(df, x=dimensions[0], y=metric)
            fig.update_layout(legend=dict(orientation="h", y=-0.3))
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type.startswith("Bar") and len(dimensions) == 2:
            fig = px.bar(
                df,
                x=dimensions[0],
                y=metric,
                color=dimensions[1],
                barmode="group"
            )
            fig.update_layout(legend=dict(orientation="h", y=-0.3))
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type.startswith("Line"):
            # Zeitachse bauen (fortlaufend)
            time_cols = []
            if {"year", "month", "day"}.issubset(df.columns):
                df["date"] = pd.to_datetime(df[["year", "month", "day"]])
                time_col = "date"
                time_cols = ["year", "month", "day"]

            elif {"year", "month"}.issubset(df.columns):
                df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
                df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

                df["date"] = pd.to_datetime(
                    df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01",
                    errors="coerce"
                )
                time_col = "date"
                time_cols = ["year", "month"]

            elif "year" in df.columns:
                time_col = "year"
                time_cols = ["year"]

            df = df.sort_values(time_col)

            # zusätzliche Dimensionen → mehrere Linien
            other_dims = [d for d in dimensions if d in df.columns and d not in time_cols]

            if other_dims:
                # mehrere Dimensionen kombinieren (z.B. VendorID | payment_type)
                if len(other_dims) > 1:
                    df["combined_dim"] = df[other_dims].astype(str).agg(" | ".join, axis=1)
                    color_dim = "combined_dim"
                else:
                    color_dim = other_dims[0]

                fig = px.line(
                    df,
                    x=time_col,
                    y=metric,
                    color=color_dim
                )
                fig.update_layout(legend=dict(orientation="h", y=-0.3))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.line_chart(df, x=time_col, y=metric)

        elif chart_type.startswith("Scatter") and len(dimensions) >= 2:
            color_dim = dimensions[2] if len(dimensions) > 2 else None
            fig = px.scatter(
                df,
                x=dimensions[0],
                y=dimensions[1],
                size=metric,
                color=color_dim
            )
            fig.update_layout(legend=dict(orientation="h", y=-0.3))
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type.startswith("3D Scatter") and len(dimensions) >= 2:
            fig = px.scatter_3d(
                df,
                x=dimensions[0],
                y=dimensions[1],
                z=metric
            )
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type.startswith("Heatmap") and len(dimensions) >= 2:
            pivot_df = df.pivot_table(
                index=dimensions[0],
                columns=dimensions[1],
                values=metric,
                aggfunc="mean"
            )
            fig = px.imshow(pivot_df)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Diagramm nicht kompatibel mit Auswahl")

    # Tabelle
    if "Tabelle" in output_mode:
        st.subheader("Tabelle")
        st.dataframe(df, use_container_width=True)

    # ============================================
    # MODEL SUMMARY (nur bei Forecast-Gruppierung)
    # ============================================
    if "forecast" in dimensions and 'all_model_summaries' in locals() and all_model_summaries:
        st.subheader("Model Bewertung")

        summary_df = pd.DataFrame(all_model_summaries)

        # Nur eine Zeile pro Modell (Kennzahlen)
        metric_cols = ["model", "aic", "nobs", "rsquared", "rsquared_adj"]
        metric_cols = [c for c in metric_cols if c in summary_df.columns]

        model_metrics_df = summary_df[metric_cols].drop_duplicates(subset=["model"])

        # Sortierung nach AIC (kleiner = besser)
        if "aic" in model_metrics_df.columns:
            model_metrics_df = model_metrics_df.sort_values("aic")

        st.dataframe(model_metrics_df, use_container_width=True)

    # Download

    st.download_button(
        f"CSV herunterladen ({metric})",
        df.to_csv(index=False),
        file_name=f"taxi_data_{metric}.csv"
    )

# ============================================
# GLOBAL CHECK (wenn alle leer)
# ============================================
if all(df.empty for df in dfs.values()):
    st.error("❌ Keine Daten gefunden")