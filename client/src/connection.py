import logging
import socket
import struct

LOG = logging.getLogger(__name__)

# FIXME: put this somewhere else
HEADER_LENGTH = 6


def parse_header(header):
    return struct.unpack('!HI', header)


def create_packet(msgtype, payload):
    header = struct.pack('!HI', msgtype, len(payload))
    return header + payload


class Connection:
    """Connection management class."""

    def __init__(self, config):
        ip, port = config['ServerIPAddress'], config.getint('ServerPort')
        LOG.info('Connecting to {}:{}'.format(ip, port))
        self.socket = socket.create_connection((ip, port))
        self.socket.settimeout(config.getfloat('SocketTimeout'))

        self.header = None
        self.payload = None

    def send(self, msgtype, payload):
        LOG.debug('Sending message: type={} size={}'.format(msgtype, len(payload)))
        self.socket.sendall(create_packet(msgtype, payload))

    def recv(self):
        if self.header is None:
            try:
                self.header = parse_header(self.socket.recv(HEADER_LENGTH))
                LOG.debug('Received header: type={} size={}'.format(self.header[0], self.header[1]))
            except socket.timeout:
                pass
        if self.header is not None:
            try:
                # FIXME: read chunks
                self.payload = self.socket.recv(self.header[1])
                LOG.debug('Received payload: {} bytes'.format(len(self.payload)))
            except socket.timeout:
                pass

        if self.payload is not None:
            # Returns the tuple (msgtype, payload)
            msgtype, payload = self.header[0], self.payload
            self.header, self.payload = None, None
            LOG.debug('Received message {}'.format(msgtype))
            return msgtype, payload
