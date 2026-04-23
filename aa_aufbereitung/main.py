"""
python3 -m venv venv
source venv/bin/activate
python3 -m pip install pandas
python3 -m pip install pyarrow
python3 -m pip install flask
python3 -m pip install waitress
python3 -m pip install scikit-learn
"""
print("Starting Lib import")
from handler.log_handler import log_handler
from handler.data_handler import data_handler
from handler.config_handler import config_handler
config = config_handler()
log = log_handler(config.getLogLevel())
log.info("Handler imported")
from flask import Flask # type: ignore
from flask import Response # type: ignore
from waitress import serve # type: ignore


log.info("Init Data-Handler")
dh = data_handler(config, log)

log.info("Load Data")
dh.load_data()

log.info("MICE Data")
dh.miceTipAmounts() # type: ignore

log.info("Data Clean-Up done")

log.info("Init Flask-Web-Server")
app = Flask(__name__)

@app.route("/raw_data")
def raw_data():
    return Response(
        dh.getCompleteRawDataframe().to_json(orient="index"),
        mimetype="application/json"
    )

@app.route("/reload_data")
def reload_data():
    config = config_handler()
    log = log_handler(config.getLogLevel())
    dh = data_handler(config)
    dh.load_data()
    dh.load_data()
    dh.miceTipAmounts()
    dh.miceTipAmounts()
    return 'done'

@app.route("/miced_data")
def miced_data():

    return Response(
        dh.getMicedDataframe().to_json(orient="index"),
        mimetype="application/json"
    )

@app.route("/files")
def files():
    return {"files": dh.getFiles()}

@app.route("/columns")
def columns():
    return {"columns": dh.getCompleteRawDataframe().columns.tolist()}

@app.route("/")
def about():
    return "About Page \n" \
    "/reload_data - reloads the data from the parquet files \n" \
    "/raw_data - returns the complete raw dataframe as json"

log.info("Start Flask Serve Server")
serve(app, host="0.0.0.0", port=8080)

log.info("Clean-Up Application Ready")