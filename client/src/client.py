from message import Message
from message import MessageField
from message import MessageType
from utils import tstamp
import logging


LOG = logging.getLogger(__name__)


class Client:
    def __init__(self, renderer, proxy):
        self.renderer = renderer
        self.proxy = proxy

        self.syncing = None
        self.delta = None
        self.sync()

    def process_message(self, msg):
        LOG.debug('Processing message {}'.format(msg))
        if self.syncing is not None and msg.msgtype == MessageType.pong:
            now = tstamp()
            self.delta = now - msg.data[MessageField.timestamp] + (now - self.syncing) / 2
            self.syncing = None
            LOG.info('Synced time with server: delta={}'.format(self.delta))
        else:
            pass

    def sync(self):
        LOG.info('Syncing time with server')
        self.syncing = tstamp()
        msg = Message(MessageType.ping, {MessageField.id: 1})
        self.proxy.push(msg)

    def start(self):
        while True:
            for msg in self.proxy.poll():
                self.process_message(msg)

            self.renderer.render()
