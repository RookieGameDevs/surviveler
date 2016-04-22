import socket

# TODO: add this to some common settings file
DEFAULT_SOCKET_TIMEOUT=0.1


class Connection:
    """Connection management class."""

    def __init__(self, host, port, timeout=DEFAULT_SOCKET_TIMEOUT):
        self.socket = socket.create_connection((host, port))
        self.socket.settimeout(0.1)

    def read(self, size=1024):
        data = None
        try:
            data = self.socket.recv(1024)
        except socket.timeout:
            pass
        return data
