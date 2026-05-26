import pandas as pd # type: ignore
import json

class day:
    def __init__(self, id):
        self.day = id
        self.id = id
        self.entries = []

    def add(self, entry):
        self.entries.append(entry)

    def to_dataframe(self):
        data = []
        for e in self.entries:
            data.append(e)
        # Python-Objekte direkt in DataFrame konvertieren
        try:
            self.dataframe = pd.json_normalize(data)
        except Exception as e:
            print("Fehler beim Konvertieren zu DataFrame:", e)
            print("Beispiel-Datenpunkt:", data[0] if data else "Keine Daten")
            raise

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