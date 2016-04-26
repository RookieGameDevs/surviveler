from enum import Enum
from enum import IntEnum
from enum import unique
import logging
import msgpack

LOG = logging.getLogger(__name__)


@unique
class MessageType(IntEnum):
    ping = 0
    pong = 1
    gamestate = 2


@unique
class MessageField(bytes, Enum):
    id = b'Id'
    timestamp = b'Tstamp'
    x_pos = b'Xpos'
    y_pos = b'Ypos'


class Message:
    """High level message class.

    Contains the message data in python format, and can be used to send data
    over the available connection.

    :param msgtype: the type of the message
    :type msgtype: :enum:`message.MessageType`

    :param data: the relevant data
    :type data: `dict`
    """

    def __init__(self, msgtype, data=None):
        self.msgtype = msgtype
        self.data = data or {}

    def encode(self):
        """Encodes and returns the message data.

        Returns the tuple (msgtype), encoded_message to be used by the
        underneath connection level.

        :return: the message type and the encoded payload
        :rtype: tuple(:enum:`message.MessageType`, bytes)
        """
        return self.msgtype, msgpack.packb(self.data)

    @classmethod
    def decode(cls, msgtype, payload):
        """Decodes the encoded payload and builds a new Message object.

        :param msgtype: the type of the message
        :type msgtype: :enum:`message.MessageType`

        :param payload: the encoded payload
        :type payload: bytes

        :return: the Message object
        :rtype: instance of :class:`message.Message`
        """
        obj = cls(msgtype, msgpack.unpackb(payload))
        return obj

    def __str__(self):
        return '<Message({})>'.format(
            MessageType(self.msgtype).name)


class MessageProxy:
    """Middle level handling message encoding/decoding.

    :param conn: the underneath connection
    :type conn: instance of :class:`connection.Connection`
    """

    def __init__(self, conn):
        LOG.info('Initializing message proxy')
        self.conn = conn

    def push(self, msg):
        """Pushes the message through the underneath connection

        :param msg: the Message object to be pushed
        :type msg: instance of :class:`message.Message`
        """
        LOG.debug('Pushing message: {} {}'.format(msg, str(msg.data)))
        self.conn.send(*msg.encode())
        LOG.debug('Pushed message: {} {}'.format(msg, str(msg.data)))

    def poll(self):
        """Polls the underneath connection and yields all the messages readed.

        :return: the Message object to be pushed
        :rtype: instance of :class:`message.Message`
        """
        while True:
            data = self.conn.recv()
            if data is None:
                break
            msgtype, payload = data
            msg = Message.decode(msgtype, payload)
            LOG.debug('Received message: {} {}'.format(msg, str(msg.data)))
            yield msg
