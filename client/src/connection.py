import logging
import socket
import struct

LOG = logging.getLogger(__name__)

HEADER = struct.Struct('!HI')
HEADER_LENGTH = HEADER.size


def parse_header(header):
    """Uses HEADER struct to unpack the header.

    :param header: the packed header
    :type header: bytes

    :return: tuple (msgtype, size)
    :rtype: tuple
    """
    return HEADER.unpack(header)


def create_packet(msgtype, payload):
    """Uses HEADER struct to prepare the header and create the packet

    :param msgtype: the message type
    :type msgtype: int

    :param payload: the encoded payload
    :type payload: bytes

    :return: the packet
    :rtype: bytes
    """
    header = HEADER.pack(msgtype, len(payload))
    return header + payload


class Connection:
    """Application layer handler.

    Handles the communication with the server as the application layer. Uses TCP
    connection to communicate with the server, and is configurable using the
    client config file.

    :param config: the network section of the config object
    :type config: :class:`configparser.SectionProxy`
    """

    def __init__(self, config):
        ip, port = config['ServerIPAddress'], config.getint('ServerPort')
        LOG.info('Connecting to {}:{}'.format(ip, port))
        self.socket = socket.create_connection((ip, port))
        self.socket.setblocking(False)
        self.chunk_size = config.getint('ChunkSize')

        self.header = None
        self.payload = None
        self.buffer = bytearray()

    def send(self, msgtype, payload):
        """Sends a packet via TCP to the server.

        :param msgtype: the message type
        :type msgtype: int

        :param payload: the encoded payload
        :type payload: bytes
        """
        LOG.debug('Writing message: {} {}'.format(msgtype, payload))
        self.socket.sendall(create_packet(msgtype, payload))
        LOG.debug('Written message: {} {}'.format(msgtype, payload))

    def recv(self):
        """Receives a single packet via TCP from the server.

        :return: tuple (msgtype, encoded_payload) if available
        :rtype: tuple or None
        """
        def read(size):
            while True:
                try:
                    chunk = min([self.chunk_size, size - len(self.buffer)])
                    d = self.socket.recv(chunk)
                    self.buffer.extend(d)
                    if len(self.buffer) == size:
                        buff, self.buffer = self.buffer, bytearray()
                        return buff
                except BlockingIOError:
                    return

        if self.header is None:
            header = read(HEADER_LENGTH)
            if header is None:
                return
            self.header = parse_header(header)
            LOG.debug('Received header: type={} size={}'.format(self.header[0], self.header[1]))

        if self.header is not None:
            payload = read(self.header[1])
            if payload is None:
                return None

            self.payload = payload
            LOG.debug('Received payload: {} bytes'.format(len(payload)))

        # Returns the tuple (msgtype, payload)
        msgtype, payload = self.header[0], self.payload
        self.header, self.payload = None, None
        LOG.debug('Received message: {} {}'.format(msgtype, payload))
        return msgtype, payload
