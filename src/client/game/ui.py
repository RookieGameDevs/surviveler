from context import Context
from events import subscriber
from game.events import ActorStatusChange
from game.events import GameModeChange
from game.events import TimeUpdate
from math import pi
from matlib.vec import Vec
from renderer.camera import OrthoCamera
from renderer.primitives import Rect
from renderer.scene import MeshNode
from renderer.scene import QuadNode
from renderer.scene import Scene
from renderer.scene import TextNode
from renderlib.core import QuadRenderProps
from renderlib.core import TextRenderProps
from renderlib.text import Text
from renderlib.texture import Texture
import logging


LOG = logging.getLogger(__name__)


class HealthBar:
    """User interface healthbar.
    """
    def __init__(self, resource, width, height):
        """Constructor.

        :param width: The width of the healthbar
        :type width: :class:`float`

        :param height: The height of the healthbar
        :type height: :class:`float`

        :param resource: The resource for the healthbar
        :type resource: :class:`loaders.Resource`
        """
        self._value = 1.0
        self.w = width
        self.h = height

        props = QuadRenderProps()
        props.color = Vec(0.2, 0.4, 1, 1)

        self.node = QuadNode((width, height), props)

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
        self._value = float(v)
        # TODO: change the visual appearance of the healthbar


class Avatar:
    """TODO: add documentation.
    """

    def __init__(self, resource, ref):
        self.w = resource.data['width']
        self.h = resource.data['height']

        texture = Texture.from_image(
            resource[ref],
            Texture.TextureType.texture_rectangle)

        props = QuadRenderProps()
        props.texture = texture

        self.node = QuadNode((self.w, self.h), props)


class UI:
    """User interface.

    This class encapsulates the user interface creation and management.
    """

    def __init__(self, resource, player_data, renderer):
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
            0,
            1)

        font = resource['font'].get_size(16)
        props = TextRenderProps()
        props.color = Vec(1, 1, 1, 1)

        # Mode node
        self.game_mode_node = self.scene.root.add_child(TextNode(
            Text(font, Context.GameMode.default.value),
            props))
        self.transform(self.game_mode_node, self.w * 0.85, 20)

        # FPS counter
        self.fps_counter_node = self.scene.root.add_child(TextNode(
            Text(font, 'FPS'),
            props))
        self.transform(self.fps_counter_node, self.w * 0.85, 0)

        # clock
        self.clock = self.scene.root.add_child(TextNode(
            Text(font, '--:--'),
            props))
        self.transform(self.clock, self.w * 0.5, 0)

        avatar_res, avatar = player_data['avatar_res'], player_data['avatar']

        # avatar
        self.avatar = Avatar(avatar_res, avatar)
        self.scene.root.add_child(self.avatar.node)
        self.transform(self.avatar.node, 0, 0)

        # healthbar
        self.health_bar = HealthBar(
            resource['health_bar'],
            avatar_res.data['width'],
            resource['health_bar'].data['height'])
        self.scene.root.add_child(self.health_bar.node)
        self.transform(self.health_bar.node, 0, avatar_res.data['width'] + 5)

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
        node.transform.ident()
        node.transform.translatev(Vec(tx, ty, -0.5))
        # TODO: is this needed?
        # node.transform.rotatev(Vec(1, 0, 0), pi / 2)

    def set_fps(self, number):
        """Set the current frame rate in FPS widget.

        :param number: Number of frames per second to visualize.
        :type number: int
        """
        self.fps_counter_node.text.string = 'FPS: {}'.format(number)

    def set_mode(self, mode=None):
        """Set the current game mode on the game mode widget.

        :param number: The game mode: None in case of default
        :type number: :enum:`context.Context.GameMode`
        """
        self.game_mode_node.text.string = '{}'.format(mode.value)

    def set_clock(self, hour, minute):
        """Set the time in clock widget.

        :param hour: Hour.
        :type hour: int

        :param minute: Minute.
        :type minute: int
        """
        self.clock.text.string = '{h:02d}:{m:02d}'.format(h=hour, m=minute)

    def render(self):
        """Render the user interface."""
        self.scene.render(self.renderer, self.camera)


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
