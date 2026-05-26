from objects.day import day
import pandas as pd # type: ignore
import json
class month:
    def __init__(self, id):
        self.id = id
        self.days = []

    def add(self, entry):
        day_id = str(entry['tpep_pickup_datetime'])[8:10]
        day_object = self.get_day_by_id(day_id)
        if day_object != None:
            day_object.add(entry)
        else:
            new_day = day(id=day_id)
            self.days.append(new_day)
            new_day.add(entry)
    def to_dataframe(self):
        data = []
        for d in self.days:
            for e in d.entries:
                data.append(e)
        # Python-Objekte direkt in DataFrame konvertieren
        try:
            self.dataframe = pd.json_normalize(data)
        except Exception as e:
            print("Fehler beim Konvertieren zu DataFrame:", e)
            print("Beispiel-Datenpunkt:", data[0] if data else "Keine Daten")
            raise
        for d in self.days:
            d.to_dataframe()
        return self.dataframe

    def get_all(self, filter):
        if not filter.validate(): return ("Invalid filter parameters", 400)
        if filter.is_aggregation():
            df = (
                self.dataframe[filter.get_columns()]
                .groupby(filter.get_aggregation_columns(), as_index=False)
                .agg(filter.get_aggregation_method())
            )
            return df.to_json(orient="records")
        elif filter.is_selection():
            return self.dataframe[filter.get_columns()].to_json(orient="records")
        return self.dataframe.to_json(orient="records")
    def get_day_by_id(self, id):
        for d in self.days:
            if d.day == id:
                return d
        return None

    def get_days(self):
        return self.days