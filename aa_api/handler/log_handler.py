import datetime

class log_handler:
    def __init__(self):
        pass

    def debug(self, message):
        date = str(datetime.datetime.now())
        print(f"{date} [DEBUG]: {message}")

    def info(self, message):
        date = str(datetime.datetime.now())
        print(f"{date} [INFO]: {message}")

    def error(self, message):
        date = str(datetime.datetime.now())
        print(f"{date} [ERROR]: {message}")