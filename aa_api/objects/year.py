from objects.month import month
import pandas as pd # type: ignore
import json
class year:
    def __init__(self, id):
        self.id = id
        self.months = []
        self.dataframe = None

    def add(self, entry):
        #self.data.append(entry)
        #print(entry)
        month_id = str(entry['tpep_pickup_datetime'])[5:7]
        #print(month_id)
        month_obejct = self.getMonthById(month_id)
        if month_obejct != None:    
            month_obejct.add(entry)
        else:
            new_month = month(id=month_id)
            self.months.append(new_month)
            new_month.add(entry)

    def toDataFrame(self):
        data = []
        for m in self.months:
            for d in m.days:
                for e in d.entries:
                    data.append(e)
        # Directly use Python objects instead of building JSON manually
        try:
            self.dataframe = pd.json_normalize(data)
        except Exception as e:
            print("Fehler beim Konvertieren zu DataFrame:", e)
            print("Beispiel-Datenpunkt:", data[0] if data else "Keine Daten")
            raise
        for m in self.months:
            m.toDataFrame()
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

    def getMonthById(self, id):
        for m in self.months:
            if m.id == id:
                return m
        return None
    
    def getMonths(self):
        return self.months