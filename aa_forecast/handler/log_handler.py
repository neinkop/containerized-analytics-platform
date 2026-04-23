import datetime

class log_handler:
    def __init__(self, log_level):
        self.log_level = log_level

    def debug(self, message):
        if self.log_level == "DEBUG":
            date = str(datetime.datetime.now())
            print(f"{date} [DEBUG]: {message}")

    def info(self, message):
        if self.log_level == "INFO" or self.log_level == "DEBUG":
            date = str(datetime.datetime.now())
            print(f"{date} [INFO]: {message}")

    def error(self, message):
        if self.log_level == "ERROR" or self.log_level == "INFO" or self.log_level == "DEBUG":
            date = str(datetime.datetime.now())
            print(f"{date} [ERROR]: {message}")