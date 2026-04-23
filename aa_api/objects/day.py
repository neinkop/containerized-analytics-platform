import pandas as pd # type: ignore
import json

class day:
    def __init__(self, id):
        self.day = id
        self.id = id
        self.entries = []

    def add(self, entry):
        self.entries.append(entry)

    def toDataFrame(self):
        data = []
        for e in self.entries:
            data.append(e)
        # Directly convert Python objects to DataFrame without building JSON strings
        try:
            self.dataframe = pd.json_normalize(data)
        except Exception as e:
            print("Fehler beim Konvertieren zu DataFrame:", e)
            print("Beispiel-Datenpunkt:", data[0] if data else "Keine Daten")
            raise
        
        return self.dataframe

    def getAll(self, filter):
        if not filter.validate(): return ("Invalid filter parameters", 400)
        if filter.isAggregation():
            df = (
                self.dataframe[filter.getColumns()]
                .groupby(filter.getAggregationColumns(), as_index=False)
                .agg(filter.getAggregationMethod())
            )
            return df.to_json(orient="records")
        elif filter.isSelection():
            return self.dataframe[filter.getColumns()].to_json(orient="records")
        return self.dataframe.to_json(orient="records")