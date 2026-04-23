class view_handler:
    def __init__(self, object_handler):
        self.object_handler = object_handler

    def show_results(self, year, month, day, filter=None):
        if year and not month and not day:
            year_object = self.object_handler.getYearById(str(year))
            if year_object != None:
                return year_object.getAll(filter)
            return f"No Data found for this year: {year}", 404
        elif month and year and not day:
            year_object = self.object_handler.getYearById(year)
            if year_object != None:
                month_object = year_object.getMonthById(month)
                if month_object != None:
                    return month_object.getAll(filter)
            return "No Data found for this month and year combination", 404
        elif day and month and year:
            year_object = self.object_handler.getYearById(year)
            if year_object != None:
                month_object = year_object.getMonthById(month)
                if month_object != None:
                    day_object = month_object.getDayById(day)
                    if day_object != None:
                        return day_object.getAll(filter)
            return "No Data found for this day, month and year combination", 404
        else:
            return "Error: No valid parameters provided", 400
    
    def data_summary(self):
        return self.object_handler.getDataSummary()
    