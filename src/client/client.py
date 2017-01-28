from context import Context
from events import send_event
from game.actions import ray_cast
from game.entities.actor import ActorType
from game.entities.map import Map
from game.entities.terrain import Terrain
from game.events import CharacterJoin
from game.events import CharacterLeave
from game.events import PlayerJoin
from game.gamestate import process_gamestate
from game.ui import UI
from itertools import count
from matlib.mat import Mat
from matlib.vec import Vec
from network import Message
from network import MessageField as MF
from network import MessageType as MT
from network import get_message_handlers
from network import message_handler
from renderer.camera import PerspCamera
from renderer.scene import LightNode
from renderer.scene import Scene
from renderlib.core import Light
from utils import as_utf8
from utils import tstamp
import logging


LOG = logging.getLogger(__name__)


class Client:
    """Client."""

    def __init__(self, character, renderer, proxy, input_mgr, res_mgr, audio_mgr, conf):
        """Constructor.

        :param character: The character name
        :type character: str

        :param renderer: The rederer
        :type renderer: :class:`renderer.Renderer`

        :param proxy: The message proxy
        :type proxy: :class:`network.message.MessageProxy`

        :param input_mgr: The input manager
        :type input_mgr: :class:`core.InputManager`

        :param res_mgr: The resource manager
        :type res_mgr: :class:`loader.ResourceManager`

        :param audio_mgr: The audio manager
        :type audio_mgr: :class:`game.audio.AudioManager`

        :param conf: Configuration
        :type conf: mapping
        """
        self.renderer = renderer
        self.proxy = proxy

        # Setup the context
        context = Context(conf)
        context.input_mgr = input_mgr
        context.res_mgr = res_mgr
        context.audio_mgr = audio_mgr

        # Setup the player
        c_res = res_mgr.get('/characters')
        c_data = c_res.data['map'][character]
        context.character_name = c_data['name']
        context.character_type = ActorType[c_data['type']]
        context.character_avatar = c_data['avatar']

        # Setup the level matrix
        map_res = res_mgr.get('/map')
        context.matrix = map_res['matrix']
        context.scale_factor = map_res.data['scale_factor']

        # Setup lights, scene, camera, terrain and map
        context.light = self.setup_light()
        context.scene = self.setup_scene(context)
        context.camera, context.ratio = self.setup_camera(context)
        context.terrain = self.setup_terrain(context)
        context.map = self.setup_map(context)

        # Setup UI
        ui_res = context.res_mgr.get('/ui')
        player_data = {
            'name': context.character_name,
            'type': context.character_type,
            'avatar': context.character_avatar,
            'avatar_res': c_res['avatar'],
        }
        context.ui = UI(ui_res, player_data, self.renderer)
        self.context = context

        # Client status variable
        self.exit = False  # Wether or not the client should stop the game loop
        self.last_update = None  # Last tick update

        self.sync_counter = count()  # The computed time delta with the server
        self._syncing = {}
        self.delta = 0  # The computed time delta with the server

        self.time_acc = 0.0  # FPS time accumulator
        self.fps_count = 0  # FPS counter

    def setup_scene(self, context):
        """Sets up the scene.

        Creates game entities and sets up the visual scene.

        :param context: Game context.
        :type context: :class:`context.Context`

        :returns: The configured scene
        :rtype: :class:`renderer.scene.Scene`
        """
        scene = Scene()

        # light_node = scene.root.add_child(LightNode(context.light))
        # light_node.transform.translatev(Vec(0, 10, 10))

        return scene

    def setup_terrain(self, context):
        """Sets up the debug terrain.

        :param context: The client context
        :type context: :class:`context.Context`

        :returns: The terrain entity
        :rtype: :class:`game.terrain.Terrain`
        """
        root = context.scene.root
        # NOTE: we are using the map resources to get the appropriate walkable
        # matrix.
        resource = context.res_mgr.get('/map')
        terrain = Terrain(resource, root)
        context.entities[terrain.e_id] = terrain
        return terrain

    def setup_map(self, context):
        """Sets up the map.

        :param context: The client context
        :type context: :class:`context.Context`

        :returns: The map entity
        :rtype: :class:`game.map.Map
        """
        resource = context.res_mgr.get('/map')
        return Map(resource, context.scene.root)

    def setup_camera(self, context):
        """Sets up camera.

        :param context: Game context.
        :type context: :class:`context.Context`

        :returns: The camera and the ratio
        :rtype: :class:`tuple`
        """
        # Aspect ratio
        aspect = self.renderer.height / float(self.renderer.width)

        camera = PerspCamera(
            25,
            1.0 / aspect,
            1,
            500)

        camera.look_at(eye=Vec(0, 20, 10), center=Vec(0, 0, 0))

        renderer_conf = context.conf['Renderer']
        w = renderer_conf.getint('width')
        h = renderer_conf.getint('height')

        p1 = ray_cast(0, 0, w, h, camera)
        p2 = ray_cast(w, 0, w, h, camera)

        ratio = (p1 - p2).mag() / w
        return camera, ratio

    def setup_light(self):
        light = Light()
        light.direction = Vec(-5, -5, -5)
        light.direction.norm()
        light.color = Vec(1, 1, 1)
        light.ambient_intensity = 0.3
        light.diffuse_intensity = 1.0

        return light

    @property
    def syncing(self):
        """True if the client is syncing with the server, otherwise False.
        """
        return len(self._syncing) > 0

    def dt(self):
        """Returns the dt from the last update.

        NOTE: this method updates the internal status of the client.

        :returns: The dt from the last update in seconds
        :rtype: float
        """
        now = tstamp()
        if self.last_update is None:
            self.last_update = now
        dt = (now - self.last_update) / 1000.0
        self.last_update = now
        return dt

    def update_fps_counter(self, dt):
        """Helper function to handle the fps counter.

        :param dt: The time delta from the last frame.
        :type dt: float
        """
        self.time_acc += dt
        self.fps_count += 1
        if self.time_acc >= 1:
            # Update fps count and reset the helper variables.
            self.time_acc -= 1
            self.context.ui.set_fps(self.fps_count)
            self.fps_count = 0

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

    def join(self, name, actor_type):
        """Sends the join request to the server.

        :param name: Player name to join with.
        :type name: str

        :param actor_type: Player type
        :type actor_type: :enum:`game.player.PlayerType`
        """
        LOG.info('Trying to join server')

        msg = Message(
            MT.join,
            {
                MF.name: name,
                MF.entity_type: actor_type
            })
        self.proxy.enqueue(msg)

    def start(self):
        """Client main loop.
        """

        self.ping()
        self.join(self.context.character_name, self.context.character_type)

        while not self.exit:
            # Compute time delta
            dt = self.dt()

            # Update FPS stats
            self.update_fps_counter(dt)

            # Poll messages from network
            self.poll_network()

            # Process user input
            self.context.input_mgr.process_input()

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
        srv_id = msg.data[MF.id]
        self.context.player_id = srv_id
        self.context.players_name_map[srv_id] = msg.data[MF.id]
        LOG.info('Joined the party with name "{}" and  ID {}'.format(
            self.context.character_name, self.context.player_id))

        # Send the proper events for the joined local player
        send_event(PlayerJoin(
            self.context.player_id, self.context.character_name))

        for srv_id, name in msg.data[MF.players].items():
            if srv_id != self.context.player_id:
                self.context.players_name_map[srv_id] = name
                send_event(CharacterJoin(srv_id, as_utf8(name)))

    @message_handler(MT.joined)
    def handle_joined(self, msg):
        """Handles player joins.

        Instantiates player entities and adds them to the game.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        character_name = as_utf8(msg.data[MF.name])
        srv_id = msg.data[MF.id]
        if srv_id != self.context.player_id:
            self.context.players_name_map[srv_id] = character_name
            send_event(CharacterJoin(srv_id, character_name))

    @message_handler(MT.leave)
    def handle_leave(self, msg):
        """Handles the leave message.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        srv_id = msg.data[MF.id]
        reason = msg.data[MF.reason]
        if not self.context.player_id or srv_id == self.context.player_id:
            LOG.info('Local player disconnected')
            self.exit = True
        else:
            LOG.info('Player "{}" disconnected'.format(srv_id))
            name = self.context.players_name_map.pop(srv_id)
            send_event(CharacterLeave(srv_id, name, reason))

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
