from game import Player
from game import get_processors
from itertools import count
from matlib import Vec3
from network import Message
from network import MessageField
from network import MessageType
from network import get_message_handlers
from network import message_handler
from renderer import OrthoCamera
from renderer import Scene
from utils import tstamp
import logging


LOG = logging.getLogger(__name__)


class Client:
    """Client class"""

    def __init__(self, renderer, proxy):
        self.proxy = proxy
        self.sync_counter = count()
        self.syncing = {}
        self.last_update = None
        self.delta = None

        self.renderer = renderer

        # field of view in game units
        fov_units = 15.0
        aspect_ratio = renderer.height / float(renderer.width)
        self.camera = OrthoCamera(
            -fov_units,                 # left plane
            fov_units,                  # right plane
            fov_units * aspect_ratio,   # top plane
            -fov_units * aspect_ratio,  # bottom plane
            10)                         # view distance
        self.camera.look_at(Vec3(0, 0, 5), Vec3(0, 0, 0))

        self.scene_setup()

    def scene_setup(self):
        """Sets up the scene.

        Creates game entities and sets up the visual scene.
        """
        self.scene = Scene()
        self.player = Player(self.scene.root)

    @message_handler(MessageType.pong)
    def pong_handler(self, msg):
        """Handle pong messages

        Sync the client time with the server, setting up the self.delta
        attribute.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        if self.syncing:
            now = tstamp()
            initial = self.syncing.pop(msg.data[MessageField.id])

            self.delta = now - msg.data[MessageField.timestamp] + (now - initial) / 2

            LOG.info('Synced time with server: delta={}'.format(self.delta))

    @message_handler(MessageType.gamestate)
    def gamestate_handler(self, msg):
        """Handle gamestate messages

        Handle the gamestate messages, actually spawning all the processors.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.debug('Processing gamestate message')
        for processor in get_processors():
            processor(msg.data)

    def process_message(self, msg):
        """Processes a message received from the server.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.info('Processing message: {} {}'.format(msg, msg.data))
        for func in get_message_handlers(msg.msgtype):
            func(self, msg)

    def sync(self):
        """Tries to guess the local delta with the server timestamps.

        Uses a message of type MessageType.ping with a random id to sync with
        the server clock guessing the lag related to ping.
        """
        LOG.info('Syncing time with server')
        sync_id = next(self.sync_counter)
        self.syncing[sync_id] = tstamp()
        msg = Message(MessageType.ping, {MessageField.id: sync_id})
        self.proxy.push(msg)

    def start(self):
        """Client main loop.

        Polls the MessageProxy and processes each message received from the
        server, renders the scene.
        """
        self.sync()
        while True:
            # compute time delta
            now = tstamp()
            if self.last_update is None:
                self.last_update = now
            dt = (now - self.last_update) / 1000.0
            self.last_update = now

            for msg in self.proxy.poll():
                self.process_message(msg)

            self.player.update(dt)

            self.renderer.clear()
            self.scene.render(self.renderer, self.camera)
            self.renderer.present()
