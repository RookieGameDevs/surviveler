from game import Entity
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


class _Client:
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

    def process_message(self, msg):
        """Processes a message received from the server.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.debug('Processing message: {} {}'.format(msg, msg.data))
        for func in get_message_handlers(msg.msgtype):
            func(msg)

    def sync(self):
        """Tries to guess the local delta with the server timestamps.

        Uses a message of type MessageType.ping with a random id to sync with
        the server clock guessing the lag related to ping.

        NOTE: this method is blocking until we receive the pong message from the
        server.
        """
        LOG.info('Syncing time with server')

        # Create, enqueue and push message
        sync_id = next(self.sync_counter)
        msg = Message(MessageType.ping, {MessageField.id: sync_id})
        self.proxy.enqueue(msg)
        self.proxy.push()

        initial = tstamp()

        # block until a pong message is received
        msg = self.proxy.wait_for(MessageType.pong)
        now = tstamp()
        self.delta = now - msg.data[MessageField.timestamp] + (now - initial) / 2
        LOG.info('Synced time with server: delta={}'.format(self.delta))

    def dt(self):
        """Returns the dt from the last update.

        :return: The dt from the last update in seconds
        :rtype: float
        """
        now = tstamp()
        if self.last_update is None:
            self.last_update = now
        dt = (now - self.last_update) / 1000.0
        self.last_update = now
        return dt

    def poll_network(self):
        """Poll the message proxy and process messages when they are complete.
        """
        for msg in self.proxy.poll():
            self.process_message(msg)

    def start(self):
        """Client main loop.

        Polls the MessageProxy and processes each message received from the
        server, renders the scene.
        """
        # Sync with server time
        self.sync()

        while True:
            # compute time delta
            dt = self.dt()

            # poll messages from network
            self.poll_network()
            # process user input
            self.input_mgr.process_input()

            self.player.update(dt)

            # rendering
            self.renderer.clear()
            self.scene.render(self.renderer, self.camera)
            self.renderer.present()
            # push messages in the proxy queue
            self.proxy.push()


class Client:
    """Client interface"""

    #: The instance of the client
    __INSTANCE = None

    def __init__(self, renderer, proxy, input_mgr):
        """Constructor.

        Just passes the arguments to the _Client constructor.

        :param renderer: The rederer
        :type renderer: :class:`renderer.Renderer`

        :param proxy: The message proxy
        :type proxy: :class:`network.message.MessageProxy`

        :param input_mgr: The input manager
        :type input_mgr: :class:`core.input.InputManager`
        """
        Client.__INSTANCE = self
        self.__client = _Client(renderer, proxy, input_mgr)

    @classmethod
    def get_instance(cls):
        """Returns the instance of the clint (aka use client as a singleton)."""
        return cls.__INSTANCE

    def start(self):
        """Wraps the _Client start method."""
        self.__client.start()

    @property
    def proxy(self):
        """The message proxy."""
        return self.__client.proxy

    @property
    def scene(self):
        """The game scene."""
        return self.__client.scene

    @property
    def camera(self):
        """The camera."""
        return self.__client.camera

    def get_entity(self, e_id):
        """Returns the entity object associated with the given entity id.

        :param e_id: The entity id.
        :type e_id: int
        """
        return Entity.get_entity(e_id)


@message_handler(MessageType.gamestate)
def gamestate_handler(msg):
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
