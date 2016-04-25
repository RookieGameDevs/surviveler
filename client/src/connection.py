import logging
import socket
import struct

LOG = logging.getLogger(__name__)

HEADER = struct.Struct('!HI')
HEADER_LENGTH = HEADER.size


def parse_header(header):
    return HEADER.unpack(header)


def create_packet(msgtype, payload):
    header = HEADER.pack(msgtype, len(payload))
    return header + payload


class Connection:
    """Connection management class."""

    def __init__(self, config):
        ip, port = config['ServerIPAddress'], config.getint('ServerPort')
        LOG.info('Connecting to {}:{}'.format(ip, port))
        self.socket = socket.create_connection((ip, port))
        self.socket.settimeout(config.getfloat('SocketTimeout'))
        self.chunk_size = config.getint('ChunkSize')

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
            except (socket.timeout, BlockingIOError):
                pass
        if self.header is not None:
            while True:
                self.payload = self.payload or bytearray()

                if len(self.payload) == self.header[1]:
                    break

                try:
                    size = (
                        self.chunk_size
                        if self.chunk_size <= self.header[1] - len(self.payload)
                        else self.header[1] - len(self.payload)
                    )
                    self.payload.extend(self.socket.recv(size))
                    LOG.debug('Received payload: {} bytes'.format(size))
                except (socket.timeout, BlockingIOError):
                    break

        if self.header is not None and self.payload is not None and len(self.payload) == self.header[1]:
            # Returns the tuple (msgtype, payload)
            msgtype, payload = self.header[0], self.payload
            self.header, self.payload = None, bytearray()
            LOG.debug('Received message {}'.format(msgtype))
            return msgtype, payload
