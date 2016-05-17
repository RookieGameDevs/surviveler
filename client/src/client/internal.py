from game import MainPlayer
from game import Player
from game import Terrain
from itertools import count
from matlib import Vec3
from network import Message
from network import MessageField
from network import MessageType
from network import get_message_handlers
from renderer import OrthoCamera
from renderer import Scene
from utils import tstamp
import logging


LOG = logging.getLogger(__name__)


class Client:
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
        # Exit flag
        self.exit = False

        # Helper variable for calculating loop dt
        self.last_update = None

        # Ping helper variables
        self.sync_counter = count()
        self._syncing = {}
        self.delta = None

        # Main client components
        self.game_cfg = game_cfg
        self.proxy = proxy
        self.renderer = renderer
        self.input_mgr = input_mgr

        # Mapping of server entities to client entities
        self.server_entities_map = {}
        # Mapping of the game entities
        self.entities = {}

    ###########################
    # Internal helper methods #
    ###########################

    def __setup_camera(self):
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

    def __setup_scene(self):
        """Sets up the scene.

        Creates game entities and sets up the visual scene.
        """
        self.scene = Scene()
        terrain = Terrain(self.scene.root, 30, 30)
        self.entities[terrain.e_id] = terrain

    def __process_message(self, msg):
        """Processes a message received from the server.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.debug('Processing message: {} {}'.format(msg, msg.data))
        for func in get_message_handlers(msg.msgtype):
            func(msg)

    def __dt(self):
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

    def __poll_network(self):
        """Poll the message proxy and process messages when they are
        complete.
        """
        for msg in self.proxy.poll():
            self.__process_message(msg)

    ####################################
    # Public internal client interface #
    ####################################

    @property
    def syncing(self):
        """True if the client is syncing with the server, otherwise False"""
        return len(self._syncing) > 0

    def add_main_player(self, name):
        """Adds the main player in the game.

        :param name: The player name
        :type name: str
        """
        return self.add_player(name, MainPlayer)

    def add_player(self, name, player_cls=Player):
        """Adds a new player in the game.

        :param name: The player name
        :type name: str

        :param player_cls: The player subclass to be used
        :type player_cls: subclass of Player
        """
        player = player_cls(name, self.scene.root)
        self.entities[player.e_id] = player
        return player.e_id

    def remove_player(self, e_id):
        """Remoives a player from the game.

        :param e_id: The id of the entity
        :type e_id: int
        """
        player = self.entities.pop(e_id)
        player.destroy()

    def ping(self):
        """Pings the server to start te timing offset calculation.
        """
        LOG.debug('Sending ping')

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
        LOG.info('Trying to join server')

        msg = Message(
            MessageType.join, {
                MessageField.name: name,
            })
        self.proxy.enqueue(msg)

    def exit(self):
        """Register for exit at the next game loop.
        """
        self.exit = True

    def start(self):
        """Client main loop.

        Polls the MessageProxy and processes each message received from the
        server, renders the scene.
        """
        # Client startup operations
        self.__setup_scene()
        self.__setup_camera()

        while not self.exit:
            # compute time delta
            dt = self.__dt()

            # poll messages from network
            self.__poll_network()

            # process user input
            self.input_mgr.process_input()

            # update entities
            for ent in self.entities.values():
                ent.update(dt)

            # rendering
            self.renderer.clear()
            self.scene.render(self.renderer, self.camera)
            self.renderer.present()
            # push messages in the proxy queue
            self.proxy.push()
