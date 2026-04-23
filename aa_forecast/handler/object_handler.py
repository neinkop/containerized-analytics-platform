import urllib.request
import urllib.error
import json
from objects.year import year
from objects.connection import connection
import time
from handler.log_handler import log_handler
import pandas as pd # type: ignore

class object_handler:
    def __init__(self, lh):
        self.source_list = []
        self.years = []
        self.lh = lh
        self.df = None

    def load_sources(self):
        self.lh.info("Loading sources from connections.list")
        #self.data_list = open("/app/data/connections.list", "r")
        self.data_list = open("../data_forecast/connections.list", "r")
        for path in self.data_list.readlines():
            if not path[0] == "#":
                path = path.replace("\n", "")
                parts = path.split(";")
                #print(parts)
                id, protocol, ip, port, column_url, data_url = parts
                connection_obj = connection(id, protocol, ip, port, column_url, data_url)
                self.source_list.append(connection_obj)
                self.lh.debug(f"Loaded source: {connection_obj}")


    def validate_sources(self):
        self.lh.info("Validating sources")
        self.load_sources()
        if not self.source_list:
            raise ValueError("source_list is empty")

        reference_columns = None
        reference_source = None

        for source in self.source_list:
            columns_url = source.getColumnUrl()
            i = 0
            done = False
            while not done and i < 3:  # Retry up to 3 times
                columns = None
                try:
                    with urllib.request.urlopen(columns_url, timeout=10) as response:
                        if response.status == 200:
                            columns = json.load(response)
                            done = True
                except json.JSONDecodeError as e:
                    raise ValueError(f"Source '{source.getConnectionString()}' returned invalid JSON for /columns: {e}")
                except urllib.error.URLError as e:
                    print(f"Attempt {i+1}: Source '{source.getConnectionString()}' is unreachable: {e}")
                if done:
                    if reference_columns is None:
                        reference_columns = columns
                        reference_source = source
                    else:
                        if columns != reference_columns:
                            self.lh.error(
                                f"Columns mismatch between sources '{reference_source.getConnectionString()}' and '{source.getConnectionString()}': "
                                f"{reference_columns} != {columns}"
                            )
                            self.source_list.remove(source)
                            #break
                else:
                    i+=1
                    time.sleep(7)  # Wait for 7 seconds before retrying
            if not done:
                self.lh.error(f"Source '{source.getConnectionString()}' unreachable at {columns_url} after 3 attempts")
                self.source_list.remove(source)
            else:
                self.lh.debug(f"Source '{source.getConnectionString()}' is valid and has matching columns.")
        if len(self.source_list) > 0:
            self.lh.info("All sources validated successfully with matching columns")
        else:
            raise ConnectionError("No sources available! All sources failed validation.")
        return True

    def load_data(self):
        self.lh.info("Loading data from sources")
        if not self.validate_sources():
            self.lh.error("Source validation failed. Data loading aborted.")
            return "Source validation failed. Data loading aborted."
        self.lh.info("Source validation successful. Proceeding with data loading.")
        response_data = []
        for source in self.source_list:
            response = urllib.request.urlopen(source.getDataUrl())
            data = json.load(response)
            response_data.append(data)
        for response in response_data:
            for entry in response.keys():
                data = response[entry]
                year_id = str(data['tpep_pickup_datetime'])[:4]
                month = str(data['tpep_pickup_datetime'])[5:7]
                day = str(data['tpep_pickup_datetime'])[8:10]
                if self.checkIfYearExists(year_id):
                    year_object = (self.getYearById(year_id))
                    year_object.add(data)
                else:
                    year_object = year(id=year_id)
                    self.years.append(year_object)
                    year_object.add(data)
        for y in self.years:
            y.toDataFrame()
        self.lh.info("Data loading completed")

    def checkIfYearExists(self, year):
        for y in self.years:
            if y.id == year:
                return True
        return False
    
    def getYearById(self, year):
        for y in self.years:
            if y.id == year:
                return y
        return None

    def getYears(self):
        return self.years
    
    def merge_df(self):
        if self.df is None:
            self.df = pd.concat([year.toDataFrame() for year in self.years], ignore_index=True)
        return self.df

    def getDataSummary(self):
        years = []
        months = []
        days = []
        for year in self.getYears():
            years.append(year.id)
            for month in year.getMonths():
                months.append(f"{year.id}-{month.id}")
                for day in month.getDays():
                    days.append(f"{year.id}-{month.id}-{day.id}")

        
        return {"years": sorted(years), "months": sorted(months), "days": sorted(days)}