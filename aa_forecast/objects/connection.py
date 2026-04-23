class connection:
    def __init__(self, id, protocol, ip, port, column_url, data_url): #protocol;ip;port;column_url;data_url
        self.id = id
        self.protocol = protocol
        self.ip = ip
        self.port = port
        self.column_url = column_url
        self.data_url = data_url

    def __str__(self):
        return f"{self.protocol}://{self.ip}:{self.port} (columns: {self.column_url}, data: {self.data_url})"
    def getConnectionString(self):
        return f"{self.protocol}://{self.ip}:{self.port}/"
    def getDataUrl(self):
        return f"{self.protocol}://{self.ip}:{self.port}/{self.data_url}"
    def getColumnUrl(self):
        return f"{self.protocol}://{self.ip}:{self.port}/{self.column_url}"
    def getPort(self):
        return self.port
    def getIp(self):
        return self.ip
    def getProtocol(self):
        return self.protocol
    def getColumnEndpoint(self):
        return self.column_url
    def getDataEndpoint(self):
        return self.data_url
    def getId(self):
        return self.id