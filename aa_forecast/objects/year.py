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
        month_obejct = self.get_month_by_id(month_id)
        if month_obejct != None:
            month_obejct.add(entry)
        else:
            new_month = month(id=month_id)
            self.months.append(new_month)
            new_month.add(entry)

    def to_dataframe(self):
        data = []
        for m in self.months:
            for d in m.days:
                for e in d.entries:
                    data.append(e)
        # Python-Objekte direkt in DataFrame konvertieren
        try:
            self.dataframe = pd.json_normalize(data)
        except Exception as e:
            print("Fehler beim Konvertieren zu DataFrame:", e)
            print("Beispiel-Datenpunkt:", data[0] if data else "Keine Daten")
            raise
        for m in self.months:
            m.to_dataframe()
        return self.dataframe


    def get_all(self):
        return self.dataframe.to_json(orient="records")

    def get_month_by_id(self, id):
        for m in self.months:
            if m.id == id:
                return m
        return None

    def get_months(self):
        return self.months