"""
python3 -m venv venv
source venv/bin/activate
python3 -m pip install urllib
python3 -m pip install json
python3 -m pip install flask
python3 -m pip install request
"""
print("Starting Lib import")
from flask import request # type: ignore
from waitress import serve # type: ignore
from flask import Flask # type: ignore
import pandas as pd # type: ignore
import json

from handler.log_handler import log_handler
from handler.object_handler import object_handler
from handler.view_handler import view_handler
from objects.filter import filter
log = log_handler()
log.info("Handler imported")

oh = object_handler(log)

oh.load_data()

vh = view_handler(oh)
app = Flask(__name__)

    
@app.route('/data/<year>/', defaults={'month': None, 'day': None})
@app.route('/data/<year>/<month>/', defaults={'day': None})
@app.route('/data/<year>/<month>/<day>')
def show_data(year, month, day):
    """print(data)
    print(year)
    print(month)
    print(day)
    print("--")"""
    filters = filter(request.args.get('filter'), request.args.get('aggr'))
    #filters.debug()
    log.debug(f"Received request for data with year={year}, month={month}, day={day} and filter={filters.getColumns()} (aggregation: {filters.getAggregationMethod()})")
    return vh.show_results(year, month, day, filter=filters)  # Pass the filter parameter

@app.route("/data_summary")
def data_summary():
    return vh.data_summary()
@app.route("/reload_data")
def reload_data():
    oh.load_data()
    return "Data reloaded successfully"
@app.route("/about")
def about():
    return "About Page"


log.info("Start Flask Serve Server")
serve(app, host="0.0.0.0", port=8090)

log.info("API Application Ready")