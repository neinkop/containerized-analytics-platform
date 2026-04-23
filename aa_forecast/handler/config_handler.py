class config_handler:
    
    def __init__(self):
        #file = open("/app/data/config", "r")
        file = open("../data_forecast/config", "r")
        """Expected config format:
            log_level=DEBUG
            #DEBUG;INFO;ERROR;NONE
            test=true
            #TRUE;FALSE
            test_rows=1000
            test_rowgroups=2"""
        for line in file.readlines():
            if line.startswith("log_level="):
                self.log_level = line.split("=")[1].strip()
            elif line.startswith("test="):
                self.test_mode = line.split("=")[1].strip().lower() == "true"
            elif line.startswith("test_rows="):
                self.test_rows = int(line.split("=")[1].strip())
            elif line.startswith("test_rowgroups="):
                self.test_row_groups = int(line.split("=")[1].strip())

    def getTestMode(self):
        return self.test_mode

    def getTestRowGroups(self):
        return self.test_row_groups

    def getTestRows(self):
        return self.test_rows

    def getLogLevel(self):
        return self.log_level