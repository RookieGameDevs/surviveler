import socket


class Connection:
    """Connection management class."""

    def __init__(self, config):
        c = config['Network']
        conf = (c['ServerIPAddress'], c.getint('ServerPort'))
        self.socket = socket.create_connection(conf)
        self.socket.settimeout(c.getfloat('SocketTimeout'))

    def read(self, size=1024):
        data = None
        try:
            data = self.socket.recv(1024)
        except socket.timeout:
            pass
        return data
