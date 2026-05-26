class config_handler:
    
    def __init__(self):
        file = open("/app/data/config", "r")
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

    def get_test_mode(self):
        return self.test_mode

    def get_test_row_groups(self):
        return self.test_row_groups

    def get_test_rows(self):
        return self.test_rows

    def get_log_level(self):
        return self.log_level