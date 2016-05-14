from game import Entity
from game import Player
from game import Terrain
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
    """Client interface"""

    #: The instance of the client
    __INSTANCE = None

    class __Client:
        """Client implementation"""

        def __init__(self, renderer, proxy, input_mgr, game_cfg):
            """Constructor.

            :param renderer: The rederer
            :type renderer: :class:`renderer.Renderer`

            :param proxy: The message proxy
            :type proxy: :class:`network.message.MessageProxy`

            :param input_mgr: The input manager
            :type input_mgr: :class:`core.InputManager`

            :param config: the network section of the config object
            :type config: :class:`configparser.SectionProxy`
            """
            self.game_cfg = game_cfg
            self.proxy = proxy
            self.sync_counter = count()
            self.last_update = None
            self._syncing = {}
            self.delta = None
            self.renderer = renderer
            self.input_mgr = input_mgr

            self.setup_scene()
            self.setup_camera()

        def setup_camera(self):
            """Sets up camera."""
            # field of view in game units
            fov = self.game_cfg.getint('fov')

            # aspect ratio
            aspect_ratio = self.renderer.height / float(self.renderer.width)

            # setup an orthographic camera with given field of view and flipped Y
            # coordinate (Y+ points down)
            self.camera = OrthoCamera(
                -fov / 2,                  # left plane
                +fov / 2,                  # right plane
                -fov / 2 * aspect_ratio,   # top plane
                +fov / 2 * aspect_ratio,   # bottom plane
                100)                       # view distance

            self.camera.look_at(eye=Vec3(0, -2.5, 5), center=Vec3(0, 0, 0))

        def setup_scene(self):
            """Sets up the scene.

            Creates game entities and sets up the visual scene.
            """
            self.scene = Scene()
            self.player = Player(self.scene.root)
            self.terrain = Terrain(self.scene.root, 30, 30)

        def process_message(self, msg):
            """Processes a message received from the server.

            :param msg: the message to be processed
            :type msg: :class:`message.Message`
            """
            LOG.debug('Processing message: {} {}'.format(msg, msg.data))
            for func in get_message_handlers(msg.msgtype):
                func(msg)

        @property
        def syncing(self):
            """True if the client is syncing with the server, otherwise False"""
            return len(self._syncing) > 0

        def ping(self):
            """Pings the server to start te timing offset calculation.
            """
            LOG.info('Sending ping')

            # Create, enqueue and push message
            sync_id = next(self.sync_counter)
            msg = Message(
                MessageType.ping, {
                    MessageField.id: sync_id,
                    MessageField.timestamp: tstamp(),
                })

            def callback():
                self._syncing[sync_id] = tstamp()

            self.proxy.enqueue(msg, callback)

        def pong(self, msg):
            """Receives pong from the server and actually calculates the offset.

            :param msg: The pong message
            :type msg: :class:`network.message.Message`
            """
            now = tstamp(0)
            sent_at = self._syncing.pop(msg.data[MessageField.id])
            self.delta = (
                now - msg.data[MessageField.timestamp] + (now - sent_at) / 2)
            LOG.info('Synced time with server: delta={}'.format(self.delta))

        def join(self, name):
            """Sends the join request to the server.

            :param name: Player name to join with.
            :type name: str
            """
            LOG.info('Sending join')

            msg = Message(
                MessageType.join, {
                    MessageField.name: name,
                })
            self.proxy.enqueue(msg)

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
            """Poll the message proxy and process messages when they are
            complete.
            """
            for msg in self.proxy.poll():
                self.process_message(msg)

        def start(self):
            """Client main loop.

            Polls the MessageProxy and processes each message received from the
            server, renders the scene.
            """
            # Sync with server time
            self.ping()

            # Send a join request
            self.join('John Doe')

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

    def __init__(self, renderer, proxy, input_mgr, game_cfg):
        """Constructor.

        Just passes the arguments to the _Client constructor.

        :param renderer: The rederer
        :type renderer: :class:`renderer.Renderer`

        :param proxy: The message proxy
        :type proxy: :class:`network.message.MessageProxy`

        :param input_mgr: The input manager
        :type input_mgr: :class:`core.InputManager`

        :param game_cfg: Game configuration
        :type game_cfg: mapping
        """
        Client.__INSTANCE = self
        self.__client = Client.__Client(renderer, proxy, input_mgr, game_cfg)

    @classmethod
    def get_instance(cls):
        """Returns the instance of the clint (aka use client as a singleton)."""
        return cls.__INSTANCE

    def start(self):
        """Wraps the _Client start method."""
        self.__client.start()

    @property
    def delta(self):
        """The tstamp offset between client and server"""
        return self.__client.delta

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

    @property
    def renderer(self):
        """The renderer."""
        return self.__client.renderer

    @property
    def config(self):
        """The game configuration."""
        return self.__client.game_cfg

    def get_entity(self, e_id):
        """Returns the entity object associated with the given entity id.

        :param e_id: The entity id.
        :type e_id: int

        :return: The required entity
        :rtype: :class:`game.Entity`
        """
        return Entity.get_entity(e_id)

    @message_handler(MessageType.pong)
    def pong(self, msg):
        self.__client.pong(msg)


@message_handler(MessageType.gamestate)
def gamestate_handler(client, msg):
    """Handle gamestate messages

    Handle the gamestate messages, actually spawning all the processors.

    Convert the server timestamp to the client one. Every timestamp in the
    gamestate messages payload from now on is to be considered comparable to
    the local timestamp (as returned by `utils.tstamp` function.

    :param client: the client interface instance
    :type client: :class:`client.Client`

    :param msg: the message to be processed
    :type msg: :class:`message.Message`
    """
    LOG.debug('Processing gamestate message')
    # Update the server timestamp adding the offset calculated after the
    # ping-pong exchange.
    msg.data[MessageField.timestamp] += client.delta or 0
    process_gamestate(msg.data)
