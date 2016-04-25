import socket


class Connection:
    """Connection management class."""

    def __init__(self, config):
        self.socket = socket.create_connection(
            (config['ServerIPAddress'], config.getint('ServerPort')))
        self.socket.settimeout(config.getfloat('SocketTimeout'))

    def read(self, size=1024):
        data = None
        try:
            data = self.socket.recv(1024)
        except socket.timeout:
            pass
        return data
