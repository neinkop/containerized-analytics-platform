from objects.day import day
import pandas as pd # type: ignore
import json
class month:
    def __init__(self, id):
        self.id = id
        self.days = []

    def add(self, entry):
        day_id = str(entry['tpep_pickup_datetime'])[8:10]
        day_object = self.getDayById(day_id)
        if day_object != None:
            day_object.add(entry)
        else:
            new_day = day(id=day_id)
            self.days.append(new_day)
            new_day.add(entry)
    def toDataFrame(self):
        data = []
        for d in self.days:
            for e in d.entries:
                data.append(e)
        # Directly convert Python objects to DataFrame without building JSON strings
        try:
            self.dataframe = pd.json_normalize(data)
        except Exception as e:
            print("Fehler beim Konvertieren zu DataFrame:", e)
            print("Beispiel-Datenpunkt:", data[0] if data else "Keine Daten")
            raise
        for d in self.days:
            d.toDataFrame()
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
    def getDayById(self, id):
        for d in self.days:
            if d.day == id:
                return d
        return None
    
    def getDays(self):
        return self.days