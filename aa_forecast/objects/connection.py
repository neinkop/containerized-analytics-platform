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
    def get_connection_string(self):
        return f"{self.protocol}://{self.ip}:{self.port}/"
    def get_data_url(self):
        return f"{self.protocol}://{self.ip}:{self.port}/{self.data_url}"
    def get_column_url(self):
        return f"{self.protocol}://{self.ip}:{self.port}/{self.column_url}"
    def get_port(self):
        return self.port
    def get_ip(self):
        return self.ip
    def get_protocol(self):
        return self.protocol
    def get_column_endpoint(self):
        return self.column_url
    def get_data_endpoint(self):
        return self.data_url
    def get_id(self):
        return self.id