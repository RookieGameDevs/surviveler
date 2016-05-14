from enum import Enum
from enum import IntEnum
from enum import unique
import logging
import msgpack

LOG = logging.getLogger(__name__)


@unique
class MessageType(IntEnum):
    """Enum of possible message types."""
    ping = 0
    pong = 1
    gamestate = 2
    move = 3


@unique
class MessageField(bytes, Enum):
    """Enum of possible message fields."""
    id = b'Id'
    timestamp = b'Tstamp'
    x_pos = b'Xpos'
    y_pos = b'Ypos'
    action = b'Action'
    action_type = b'ActionType'
    speed = b'Speed'
    entities = b'Entities'


class Message:
    """High level message class.

    Contains the message data in python format, and can be used to send data
    over the available connection.
    """

    def __init__(self, msgtype, data=None):
        """Constructor.
        :param msgtype: the type of the message
        :type msgtype: :enum:`message.MessageType`

        :param data: the relevant data
        :type data: `dict`
        """
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
        :rtype: :class:`message.Message`
        """
        obj = cls(msgtype, msgpack.unpackb(payload))
        return obj

    def __str__(self):
        return '<Message({})>'.format(
            MessageType(self.msgtype).name)


class MessageProxy:
    """Middle level handling message encoding/decoding.
    """

    def __init__(self, conn):
        """Constructor.

        :param conn: the underneath connection
        :type conn: :class:`connection.Connection`
        """
        LOG.info('Initializing message proxy')
        self.conn = conn
        self.msg_queue = []

    def enqueue(self, msg, callback=lambda: None):
        """Enqueue the message.

        The message is going to be sent during the next push.

        :param msg: the Message object to be pushed
        :type msg: :class:`message.Message`

        :param callback: Callback to be called when the message is pushed
        :type callback: function or None
        """
        LOG.debug('Enqueueing message: {} {}'.format(msg, str(msg.data)))
        self.msg_queue.append((msg, callback))

    def push(self):
        """Pushes the message through the underneath connection"""
        while len(self.msg_queue):
            msg, cb = self.msg_queue.pop(0)
            LOG.debug('Pushing message: {} {}'.format(msg, str(msg.data)))
            self.conn.send(*msg.encode())
            LOG.debug('Pushed message: {} {}'.format(msg, str(msg.data)))
            cb()

    def wait_for(self, msgtype):
        """Polls the connection waiting for a specific message.

        :param msgtype: The message type we are waiting for
        :type msgtype: :class:`network.message.MessageType`

        :return: The message.
        :rtype: :class:`network.message.Message`
        """
        with self.conn.blocking():
            while True:
                for msg in self.poll(MessageType.pong):
                    return msg

    def poll(self, msgtype=None):
        """Polls the underneath connection and yields all the messages readed.

        :return: the Message object to be pushed
        :rtype: :class:`message.Message`
        """
        while True:
            data = self.conn.recv()
            if data is None:
                break
            mt, payload = data
            if msgtype and mt != msgtype:
                LOG.debug('Discarded message: {}]'.format(mt))
                continue
            msg = Message.decode(mt, payload)
            LOG.debug('Received message: {} {}'.format(msg, str(msg.data)))
            yield msg
