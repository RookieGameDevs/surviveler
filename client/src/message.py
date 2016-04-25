from enum import Enum
from enum import IntEnum
from enum import unique
import msgpack


@unique
class MessageType(IntEnum):
    ping = 0
    pong = 1
    # FIXME: Remove me
    misc = 2


@unique
class MessageField(bytes, Enum):
    id = b'id'
    timestamp = b'tstamp'


class Message:
    def __init__(self, msgtype, data=None):
        self.msgtype = msgtype
        self.data = data or {}

    def encode(self):
        return self.msgtype, msgpack.packb(self.data)

    @classmethod
    def decode(cls, msgtype, payload):
        obj = cls(msgtype, msgpack.unpackb(payload))
        return obj

    def __str__(self):
        return '<Message({})>'.format(
            MessageType(self.msgtype).name)


class MessageProxy:
    def __init__(self, conn):
        self.conn = conn

    def push(self, msg):
        self.conn.send(*msg.encode())

    def poll(self):
        data = self.conn.recv()
        while data is not None:
            msgtype, payload = data
            yield Message.decode(msgtype, payload)
            data = self.conn.recv()
