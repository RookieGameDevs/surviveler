from message import Message
from message import MessageField
from message import MessageType
from utils import tstamp
import logging


LOG = logging.getLogger(__name__)


class Client:
    """Client class"""

    def __init__(self, renderer, proxy):
        self.renderer = renderer
        self.proxy = proxy

        self.syncing = None
        self.delta = None
        self.sync()

    def process_message(self, msg):
        """Processes a message received from the server.

        :param msg: the message to be processed
        :type msg: instance of :class:`message.Message`
        """
        LOG.debug('Processing message {}'.format(msg))
        if self.syncing is not None and msg.msgtype == MessageType.pong:
            now = tstamp()
            self.delta = now - msg.data[MessageField.timestamp] + (now - self.syncing) / 2
            self.syncing = None
            LOG.info('Synced time with server: delta={}'.format(self.delta))
        else:
            pass

    def sync(self):
        """Tries to guess the local delta with the server timestamps.

        Uses a message of type MessageType.ping with a random id to sync with
        the server clock guessing the lag related to ping.
        """
        LOG.info('Syncing time with server')
        self.syncing = tstamp()
        msg = Message(MessageType.ping, {MessageField.id: 1})
        self.proxy.push(msg)

    def start(self):
        """Client main loop.

        Polls the MessageProxy and processes each message received from the
        server, renders the scene.
        """
        while True:
            for msg in self.proxy.poll():
                self.process_message(msg)

            self.renderer.render()
