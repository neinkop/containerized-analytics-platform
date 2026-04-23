Abfrage: http://127.0.0.1:8090/data/2025/07/01?filter=VendorID,forecast,passenger_count&aggr=count,VendorID,forecast
Rückmeldung: [{"VendorID":1,"forecast":"%NAME%","passenger_count":272},{"VendorID":2,"forecast":"%NAME%","passenger_count":1206},{"VendorID":7,"forecast":"%NAME%","passenger_count":16}]

## Mögliche Gruppierung/Aggregierung
- `VendorID` --> [1, 2, 6, 7]
- `payment_type` --> [0-6]
- `RatecodeID` --> [1, 2, 3, 4, 5, 6, 99]
- `store_and_fwd_flag` --> [N, Y]
- `pickup_year` --> [2026]
- `pickup_month` --> [1-12]
- `pickup_day` --> [1-31]
- `pickup_hour` --> [0-23]
- `dropoff_year` --> [2026]
- `dropoff_month` --> [1-12]
- `dropoff_day` --> [1-31]
- `dropoff_hour` --> [0-23]


## Mögliche Werte
- `total_amount`
- `fare_amount`
- `trip_distance`
- `tip_amount`
- `passenger_count`
- `tolls_amount`

Trainingsdaten: Jan-Dez 2025
Testdaten: Jan 2026
Datenquelle: Aufbereitungscontainer

Identifikation:
- Jahreszeit (0-3)/(winter/spring/summer/fall)
- Wochentag (0-6)(monday/tuesday/wednesday/...)
- Wochenende ja/nein
- Feiertag ja/nein
- vor Feiertag ja/nein
- nach Feiertag ja/nein
- Rush-Hour ja/nein
- is_event ja/nein
- dow_sin/cos
- month_sin/cos
#weekday":1,"is_weekend":0,"season":2,"is_holiday":0,"is_school_holiday":0,"before_holiday":0,"after_holiday":0,"is_rush_hour":0,"is_event":0,"dow_sin":0.7818314825,"dow_cos":0.6234898019,"month_sin":-0.5,"month_cos":-0.8660254038



Sinus/Cosinus Zyklus





['season', 'month_sin', 'month_cos', 'weekday', 'is_weekend', 'is_holiday', 'is_school_holiday', 'before_holiday', 'after_holiday', 'is_event', 'dow_sin', 'dow_cos', 'payment_type', 'pickup_day', 'passenger_count']
['payment_type', 'month_sin', 'month_cos', 'season', 'dow_sin', 'dow_cos', 'weekday', 'is_weekend', 'is_holiday', 'is_school_holiday', 'before_holiday', 'after_holiday', 'is_event']
