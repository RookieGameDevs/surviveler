from context import Context
from datetime import datetime
from events import subscriber
from game.events import ActorStatusChange
from game.events import CharacterJoin
from game.events import CharacterLeave
from game.events import GameModeChange
from game.events import TimeUpdate
from math import pi
from matlib import Vec
from renderer import Font
from renderer import GeometryNode
from renderer import OrthoCamera
from renderer import Rect
from renderer import Scene
from renderer import SceneNode
from renderer import TextNode
import logging


LOG = logging.getLogger(__name__)


class HealthBar:
    """User interface healthbar.
    """
    def __init__(self, width, height, resource):
        """Constructor.

        :param width: The width of the healthbar
        :type width: :class:`float`

        :param height: The height of the healthbar
        :type height: :class:`float`

        :param resource: The resource for the healthbar
        :type resource: :class:`loaders.Resource`
        """
        self._value = 1
        self.w = width
        self.h = height

        mesh = resource.userdata.get('mesh')
        if not mesh:
            mesh = Rect(self.w, self.h)
            resource.userdata['mesh'] = mesh

        shader = resource['shader']

        params = {
            'width': float(self.w),
            'value': self._value,
            'bg_color': Vec(0, 0, 0, 1),
            'fg_color': Vec(0.2, 0.4, 1, 1),
        }

        self.node = GeometryNode(
            mesh,
            shader,
            params=params,
            enable_light=False)

    @property
    def value(self):
        """Returns the value [0,1] of that is currently displayed.

        :returns: The value of the health bar
        :rtype: :class:`float`
        """
        return self._value

    @value.setter
    def value(self, v):
        """Sets the value [0,1] to be displayed.

        :param v: The value of the health bar
        :type v: :class:`float`
        """
        self._value = v
        self.node.params['value'] = v


class UI:
    """User interface.

    This class encapsulates the user interface creation and management.
    """

    def __init__(self, resource, renderer):
        """Constructor.

        :param resource: The ui resource
        :type resource: :class:`loaders.Resource`

        :param renderer: Renderer to use for UI rendering.
        :type renderer: :class:`renderer.Renderer`
        """
        self.renderer = renderer
        self.w = renderer.width
        self.h = renderer.height
        self.scene = Scene()
        self.camera = OrthoCamera(
            -self.w / 2, +self.w / 2,
            +self.h / 2, -self.h / 2,
            0, 1)

        # log
        self.log_line_height = 18
        self.log_height = 0
        self.log_color = Vec(0.7, 0.7, 0.7)
        self.log_font = Font(resource['font'], 14)
        self.log_shader = resource['shader']
        self.log_node = self.scene.root.add_child(SceneNode())

        # Mode node
        self.game_mode_node = self.scene.root.add_child(TextNode(
            self.log_font,
            self.log_shader,
            Context.GameMode.default.value,
            self.log_color))
        self.transform(self.game_mode_node, self.w * 0.85, 20)

        # FPS counter
        self.fps_counter_node = self.scene.root.add_child(TextNode(
            self.log_font,
            self.log_shader,
            'FPS',
            self.log_color))
        self.transform(self.fps_counter_node, self.w * 0.85, 0)

        # clock
        self.clock = self.scene.root.add_child(TextNode(
            self.log_font,
            self.log_shader,
            '--:--',
            self.log_color))
        self.transform(self.clock, self.w * 0.5, 0)

        # healthbar
        self.health_bar = HealthBar(
            self.w, resource['health_bar'].data['height'],
            resource['health_bar'])
        self.scene.root.add_child(self.health_bar.node)
        self.transform(
            self.health_bar.node,
            0, self.h - resource['health_bar'].data['height'])

    def transform(self, node, x, y):
        """Transform the UI scene node from screen space to scene space.

        :param node: Scene node to transform.
        :type node: :class:`renderer.scene.SceneNode`

        :param x: Screen X coordinate.
        :type x: float

        :param y: Screen Y coordinate.
        :type y: float
        """
        tx = x - self.w / 2
        ty = self.h / 2 - y
        node.transform.identity()
        node.transform.translate(Vec(tx, ty, -0.5))
        node.transform.rotate(Vec(1, 0, 0), pi / 2)

    def set_fps(self, number):
        """Set the current frame rate in FPS widget.

        :param number: Number of frames per second to visualize.
        :type number: int
        """
        self.fps_counter_node.text = 'FPS: {}'.format(number)

    def set_mode(self, mode=None):
        """Set the current game mode on the game mode widget.

        :param number: The game mode: None in case of default
        :type number: :enum:`context.Context.GameMode`
        """
        self.game_mode_node.text = '{}'.format(mode.value)

    def set_clock(self, hour, minute):
        """Set the time in clock widget.

        :param hour: Hour.
        :type hour: int

        :param minute: Minute.
        :type minute: int
        """
        self.clock.text = '{h:02d}:{m:02d}'.format(h=hour, m=minute)

    def log(self, msg):
        """Log a message on screen console.

        :param msg: Message to log.
        :type msg: str
        """
        if self.log_height >= self.w - self.log_line_height:
            self.log_node.children = []

        txt = self.log_node.add_child(TextNode(
            self.log_font,
            self.log_shader,
            msg,
            self.log_color))
        self.transform(txt, 0, self.log_height)

        self.log_height += self.log_line_height

    def render(self):
        """Render the user interface."""
        self.scene.render(self.renderer, self.camera)


@subscriber(CharacterJoin)
def log_join(evt):
    """Logs the name and ID of the joined character to UI console."""
    if evt.name:
        evt.context.ui.log('[{}] {} joined with ID {}'.format(
            datetime.now().time().replace(microsecond=0).isoformat(),
            evt.name,
            evt.srv_id))


@subscriber(CharacterLeave)
def log_leave(evt):
    """Logs the name of the character which just left the party."""
    evt.context.ui.log('[{}] {} left the game:'.format(
        datetime.now().time().replace(microsecond=0).isoformat(),
        evt.name,
        evt.reason or 'disconnected'))


@subscriber(TimeUpdate)
def update_time(evt):
    """Updates the UI clock."""
    evt.context.ui.set_clock(evt.hour, evt.minute)


@subscriber(GameModeChange)
def show_gamemode(evt):
    """In case we are in a gamemode different from the default one shows it."""
    context = evt.context
    if evt.cur != context.GameMode.default:
        context.ui.set_mode(evt.cur)
    else:
        context.ui.set_mode(context.GameMode.default)


@subscriber(ActorStatusChange)
def player_health_change(evt):
    """Updates the number of hp of the actor.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    srv_id = evt.srv_id
    if srv_id == context.player_id and srv_id in context.server_entities_map:
        e_id = context.server_entities_map[evt.srv_id]
        actor = context.entities[e_id]
        actor.health = evt.new, actor.health[1]
        context.ui.health_bar.value = evt.new / actor.health[1]
