from message import Message
from message import MessageField
from message import MessageType
from utils import tstamp


class Client:
    def __init__(self, renderer, proxy):
        self.renderer = renderer
        self.proxy = proxy

        self.syncing = None
        self.delta = None
        self.sync()

    def process_message(self, msg):
        if self.syncing is not None and msg.msgtype == MessageType.pong:
            now = tstamp()
            self.delta = now - msg.data[MessageField.timestamp] + (now - self.syncing) / 2
            self.syncing = None
        else:
            print(msg)

    def sync(self):
        self.syncing = tstamp()
        msg = Message(MessageType.ping, {MessageField.id: 1})
        self.proxy.push(msg)

    def start(self):
        while True:
            for msg in self.proxy.poll():
                self.process_message(msg)

            self.renderer.render()
