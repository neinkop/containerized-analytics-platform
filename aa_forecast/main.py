"""
python3 -m venv venv
source venv/bin/activate
python3 -m pip install pandas
python3 -m pip install flask
python3 -m pip install waitress
python3 -m pip install requests
python3 -m pip install statmodels
python3 -m pip install holidays
"""
print("Starting Handler import")
from handler.config_handler import config_handler
config = config_handler()
from handler.log_handler import log_handler
log = log_handler(config.getLogLevel())
from handler.object_handler import object_handler
from objects.filter import filter

log.info("Handler imported")
log.info("Starting Lib import")
from flask import request # type: ignore
from waitress import serve # type: ignore
from flask import Flask # type: ignore
import pandas as pd # type: ignore
import json
import datetime
log.info("Libs imported")

#import holidays # type: ignore

from modeler import modeler

def generate_dates(years, months):
    days = []
    months_out = []
    years_out = []

    for year in years:
        years_out.append(str(year))
        for month in months:
            # Anzahl Tage im Monat holen
            import calendar
            from datetime import date 
            num_days = calendar.monthrange(year, month)[1]

            # Monat hinzufügen (YYYY-MM)
            months_out.append(f"{year}-{month:02d}")

            # Alle Tage generieren
            for day in range(1, num_days + 1):
                d = date(year, month, day)
                days.append(d.strftime("%Y-%m-%d"))

    return {
        "days": days,
        "months": months_out,
        "years": years_out
    }
oh = object_handler(log)
oh.load_data()
log.debug("Data loaded, now merging into single DataFrame...")
md = modeler(log, oh.merge_df())
log.info("Modeler initialized with merged DataFrame - Amount of rows: " + str(len(md.df)))
log.debug("Modeler DataFrame head: " + str(md.df.head(2).to_json(orient='index')))



app = Flask(__name__)

    
@app.route('/data/<year>/', defaults={'month': None, 'day': None})
@app.route('/data/<year>/<month>/', defaults={'day': None})
@app.route('/data/<year>/<month>/<day>')
def show_data(year, month, day):
    log.debug(f"Received request for data with year={year}, month={month}, day={day} and filter={request.args.get('filter')} (aggregation: {request.args.get('aggr')})")
    filters = filter(request.args.get('filter'), request.args.get('aggr'))
    if not filters.validate(): return ("Invalid filter parameters (main)", 400)
    if not filters.isAggregation(): return ("No aggregation parameters provided", 400)
    return md.handle(year, month, day, filters) 
    
@app.route("/data_summary")
def data_summary():
    return generate_dates([2026], [1])
@app.route("/reload_data")
def reload_data():
    oh.load_data()
    md = modeler(log, oh.merge_df())
    log.info("Modeler re-initialized with merged DataFrame - Amount of rows: " + str(len(md.df)))
    return "Data reloaded successfully"
@app.route("/about")
def about():
    return "About Page"

log.info("Start Flask Serve Server")
serve(app, host="0.0.0.0", port=9000)