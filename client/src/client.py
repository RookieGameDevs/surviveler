from game import Player
from game import process_gamestate
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

    def __init__(self, renderer, proxy, input_mgr):
        self.proxy = proxy
        self.sync_counter = count()
        self.last_update = None
        self.delta = None

        self.renderer = renderer
        self.input_mgr = input_mgr

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

    @message_handler(MessageType.gamestate)
    def gamestate_handler(self, msg):
        """Handle gamestate messages

        Handle the gamestate messages, actually spawning all the processors.

        Convert the server timestamp to the client one. Every timestamp in the
        gamestate messages payload from now on is to be considered comparable to
        the local timestamp (as returned by `utils.tstamp` function.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.debug('Processing gamestate message')
        # TODO: uncomment me when the server will give back a timestamp in the
        # gamestate.
        # msg.data[MessageField.timestamp] += self.delta or 0
        process_gamestate(msg.data)

    def process_message(self, msg):
        """Processes a message received from the server.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.debug('Processing message: {} {}'.format(msg, msg.data))
        for func in get_message_handlers(msg.msgtype):
            func(self, msg)

    def sync(self):
        """Tries to guess the local delta with the server timestamps.

        Uses a message of type MessageType.ping with a random id to sync with
        the server clock guessing the lag related to ping.

        NOTE: this method is blocking until we receive the pong message from the
        server.
        """
        LOG.info('Syncing time with server')

        # Utility function to filter out non-pong messages
        is_pong = lambda msg: msg.msgtype == MessageType.pong

        # Create, enqueue and push message
        sync_id = next(self.sync_counter)
        msg = Message(MessageType.ping, {MessageField.id: sync_id})
        self.proxy.enqueue(msg)
        self.proxy.push()

        initial = tstamp()

        # block until a pong message is received
        while True:
            for msg in filter(is_pong, self.proxy.poll()):
                now = tstamp()
                self.delta = now - msg.data[MessageField.timestamp] + (now - initial) / 2
                LOG.info('Synced time with server: delta={}'.format(self.delta))
                return

    def start(self):
        """Client main loop.

        Polls the MessageProxy and processes each message received from the
        server, renders the scene.
        """
        # Sync with server time
        self.sync()

        while True:
            # compute time delta
            now = tstamp()
            if self.last_update is None:
                self.last_update = now
            dt = (now - self.last_update) / 1000.0
            self.last_update = now

            # poll messages from network
            for msg in self.proxy.poll():
                self.process_message(msg)

            # process user input
            self.input_mgr.process_input()

            self.player.update(dt)

            self.renderer.clear()
            self.scene.render(self.renderer, self.camera)
            self.renderer.present()

            # push messages in the proxy queue
            self.proxy.push()
