from context import Context
from events import send_event
from game import Terrain
from game import UI
from game import process_gamestate
from game.events import CharacterJoin
from game.events import CharacterLeave
from game.events import PlayerJoin
from itertools import count
from matlib import Vec3
from network import Message
from network import MessageField as MF
from network import MessageType as MT
from network import get_message_handlers
from network import message_handler
from renderer import OrthoCamera
from renderer import Scene
from utils import as_utf8
from utils import tstamp
import logging


LOG = logging.getLogger(__name__)


class Client:
    """Client."""

    def __init__(self, player_name, renderer, proxy, input_mgr, conf):
        """Constructor.

        Just passes the arguments to the _Client constructor.

        :param player_name: The player name
        :type player_name: str

        :param renderer: The rederer
        :type renderer: :class:`renderer.Renderer`

        :param proxy: The message proxy
        :type proxy: :class:`network.message.MessageProxy`

        :param input_mgr: The input manager
        :type input_mgr: :class:`core.InputManager`

        :param conf: Configuration
        :type conf: mapping
        """
        self.renderer = renderer
        self.proxy = proxy
        self.input_mgr = input_mgr

        # Setup the context
        context = Context(conf)
        context.scene = self.setup_scene(context)
        context.camera = self.setup_camera(context)
        context.ui = UI(self.renderer)
        context.player_name = player_name
        self.context = context

        # Client status variable
        self.exit = False  # Wether or not the client should stop the game loop
        self.last_update = None  # Last tick update

        self.sync_counter = count()  # The computed time delta with the server
        self._syncing = {}
        self.delta = 0  # The computed time delta with the server

    def setup_scene(self, context):
        """Sets up the scene.

        Creates game entities and sets up the visual scene.

        :param context: Game context.
        :type context: :class:`context.Context`

        :return: The configured scene
        :rtype: :class:`renderer.scene.Scene`
        """
        scene = Scene()
        terrain = Terrain(scene.root, 30, 30)
        context.entities[terrain.e_id] = terrain
        return scene

    def setup_camera(self, context):
        """Sets up camera.

        :param context: Game context.
        :type context: :class:`context.Context`

        :return: The camera
        :rtype: :class:`renderer.camera.Camera`
        """
        # Field of view in game units
        fov = context.conf['Game'].getint('fov')

        # Aspect ratio
        aspect = self.renderer.height / float(self.renderer.width)

        # Setup an orthographic camera with given field of view and flipped Y
        # coordinate (Y+ points down)
        camera = OrthoCamera(
            -fov / 2,            # left plane
            +fov / 2,            # right plane
            -fov / 2 * aspect,   # top plane
            +fov / 2 * aspect,   # bottom plane
            100)                 # view distance

        camera.look_at(eye=Vec3(0, -2.5, 5), center=Vec3(0, 0, 0))

        return camera

    @property
    def syncing(self):
        """True if the client is syncing with the server, otherwise False.
        """
        return len(self._syncing) > 0

    @property
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

    def process_message(self, msg):
        """Processes a message received from the server.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.debug('Processing message: {} {}'.format(msg, msg.data))
        for func in get_message_handlers(msg.msgtype):
            func(self, msg)

    def poll_network(self):
        """Polls the message proxy and process messages when they are complete.
        """
        for msg in self.proxy.poll():
            self.process_message(msg)

    def ping(self):
        """Pings the server to start te timing offset calculation.
        """
        LOG.debug('Sending ping')

        # Create and enqueue the ping message
        sync_id = next(self.sync_counter)
        msg = Message(MT.ping, {MF.id: sync_id, MF.timestamp: tstamp()})

        def callback():
            self._syncing[sync_id] = tstamp()

        self.proxy.enqueue(msg, callback)

    def join(self, name):
        """Sends the join request to the server.

        :param name: Player name to join with.
        :type name: str
        """
        LOG.info('Trying to join server')

        msg = Message(MT.join, {MF.name: name})
        self.proxy.enqueue(msg)

    def start(self):
        """Client main loop.
        """

        self.ping()
        self.join(self.context.player_name)

        while not self.exit:
            # Compute time delta
            dt = self.dt

            # Poll messages from network
            self.poll_network()

            # Process user input
            self.input_mgr.process_input()

            # Update entities
            for ent in self.context.entities.values():
                ent.update(dt)

            # rendering
            self.renderer.clear()
            self.context.scene.render(self.renderer, self.context.camera)
            self.context.ui.render()
            self.renderer.present()

            # Enqueue messages in context and emtpy the queue
            for msg in self.context.msg_queue:
                self.proxy.enqueue(msg)
            self.context.msg_queue = []

            # Push messages in the proxy queue
            self.proxy.push()

    @message_handler(MT.pong)
    def pong(self, msg):
        """Receives pong from the server and actually calculates the offset.

        :param msg: The pong message
        :type msg: :class:`network.message.Message`
        """
        now = tstamp(0)
        sent_at = self._syncing.pop(msg.data[MF.id])
        self.delta = (
            now - msg.data[MF.timestamp] + (now - sent_at) / 2)
        LOG.info('Synced time with server: delta={}'.format(self.delta))

    @message_handler(MT.stay)
    def handle_stay(self, msg):
        """Handles stay response from server.

        Assigns the client a server provided id, which uniquely identifies the
        controlled player entity.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        self.context.player_id = msg.data[MF.id]
        LOG.info('Joined the party with name "{}" and  ID {}'.format(
            self.context.player_name, self.context.player_id))

        # Send the proper events for the joined local player
        send_event(PlayerJoin(self.context.player_id, self.context.player_name))

        for srv_id, name in msg.data[MF.players].items():
            send_event(CharacterJoin(srv_id, name))

    @message_handler(MT.joined)
    def handle_joined(self, msg):
        """Handles player joins.

        Instantiates player entities and adds them to the game.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        player_name = as_utf8(msg.data[MF.name])
        srv_id = msg.data[MF.id]
        send_event(CharacterJoin(srv_id, player_name))

    @message_handler(MT.leave)
    def handle_leave(self, msg):
        """Handles the leave message.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        srv_id = msg.data[MF.id]
        reason = msg.data[MF.reason]
        if srv_id == self.context.player_id:
            LOG.info('Local player disconnected')
            self.exit = True
        else:
            LOG.info('Player "{}" disconnected'.format(srv_id))
            send_event(CharacterLeave(srv_id, reason))

    @message_handler(MT.gamestate)
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
        # Update the server timestamp adding the offset calculated after the
        # ping-pong exchange.
        msg.data[MF.timestamp] += self.delta or 0
        process_gamestate(msg.data)
