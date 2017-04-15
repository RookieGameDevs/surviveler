from context import Context
from events import subscriber
from game.events import ActorStatusChange
from game.events import GameModeChange
from game.events import TimeUpdate
from matlib.vec import Vec
from renderlib.camera import OrthographicCamera
from renderlib.quad import Quad
from renderlib.quad import QuadProps
from renderlib.scene import Scene
from renderlib.text import Text
from renderlib.text import TextProps
from renderlib.texture import Texture
import logging


LOG = logging.getLogger(__name__)


class HealthBar:
    """User interface healthbar."""

    def __init__(self, scene, resource, value=1.0):
        """Constructor.

        :param scene: Scene to add the healthbar to.
        :type scene: :class:`renderlib.scene.Scene`

        :param resource: The resource for the healthbar
        :type resource: :class:`loaders.Resource`

        :param value: Initial health bar value.
        :tyep value: float
        """
        self.resource = resource
        self._value = value

        width = resource.data['width']
        height = resource.data['height']
        left, right, top, bottom = resource.data['borders']

        fg_texture = Texture.from_image(
            resource['fg_texture'],
            Texture.TextureType.texture_rectangle)
        bg_texture = Texture.from_image(
            resource['bg_texture'],
            Texture.TextureType.texture_rectangle)

        fg_props = QuadProps()
        fg_props.texture = fg_texture
        fg_props.borders.left = left
        fg_props.borders.right = right
        fg_props.borders.top = top
        fg_props.borders.bottom = bottom

        bg_props = QuadProps()
        bg_props.texture = bg_texture
        bg_props.borders.left = left
        bg_props.borders.right = right
        bg_props.borders.top = top
        bg_props.borders.bottom = bottom

        self.bg_quad = Quad(width, height)
        self.bg_obj = scene.add_quad(self.bg_quad, bg_props)
        self.bg_obj.position.z = -0.1

        self.fg_quad = Quad(width, height)
        self.fg_obj = scene.add_quad(self.fg_quad, fg_props)

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
        # change the width of foreground quad
        self.fg_quad.width = self.resource.data['width'] * v


class Avatar:
    """Character avatar widget."""

    def __init__(self, scene, resource, ref):
        """Constructor.

        :param scene: Scene to add the avatar widget to.
        :type scene: :class:`renderlib.class.Scene`

        :param resource: The resource for the healthbar
        :type resource: :class:`loaders.Resource`

        :param ref: Avatar reference.
        :type ref: string
        """
        self.w = resource.data['width']
        self.h = resource.data['height']

        texture = Texture.from_image(
            resource[ref],
            Texture.TextureType.texture_rectangle)

        props = QuadProps()
        props.texture = texture
        self.obj = scene.add_quad(Quad(self.w, self.h), props)


class UI:
    """User interface.

    This class encapsulates the user interface creation and management.
    """

    def __init__(self, resource, width, height, player_data):
        """Constructor.

        :param resource: The UI resource.
        :type resource: :class:`loaders.Resource`

        :param width: UI width in pixels.
        :type width: int

        :param height: UI height in pixels.
        :type height: int

        :param player_data: Player resource.
        :type player_ddata: :class:`loaders.Resource`
        """
        self.w = width
        self.h = height
        self.scene = Scene()
        self.camera = OrthographicCamera(
            -self.w / 2,  # left
            +self.w / 2,  # right
            +self.h / 2,  # top
            -self.h / 2,  # bottom
            0,            # near
            1)            # far

        font = resource['font'].get_size(16)
        props = TextProps()
        props.color = Vec(1, 1, 1, 1)

        # Mode node
        self.game_mode_text = Text(font, Context.GameMode.default.value)
        self.game_mode = self.scene.add_text(self.game_mode_text, props)
        self.transform(self.game_mode, self.w * 0.85, 20)

        # FPS counter
        self.fps_counter_text = Text(font, 'FPS')
        self.fps_counter = self.scene.add_text(self.fps_counter_text, props)
        self.transform(self.fps_counter, self.w * 0.85, 0)

        # clock
        self.clock_text = Text(font, '--:--')
        self.clock = self.scene.add_text(self.clock_text, props)
        self.transform(self.clock, self.w * 0.5, 0)

        # avatar
        avatar_res, avatar = player_data['avatar_res'], player_data['avatar']
        self.avatar = Avatar(self.scene, avatar_res, avatar)
        self.transform(self.avatar.obj, 0, 0)

        # healthbar
        self.health_bar = HealthBar(self.scene, resource['health_bar'])
        self.transform(self.health_bar.bg_obj, 0, avatar_res.data['width'] + 5)
        self.transform(self.health_bar.fg_obj, 0, avatar_res.data['width'] + 5)

    def transform(self, obj, x, y):
        """Transform the UI scene node from screen space to scene space.

        :param obj: Scene object to transform.
        :type obj: :class:`renderlib.scene.Object`

        :param x: Screen X coordinate.
        :type x: float

        :param y: Screen Y coordinate.
        :type y: float
        """
        obj.position.x = x - self.w / 2
        obj.position.y = self.h / 2 - y

    def set_fps(self, number):
        """Set the current frame rate in FPS widget.

        :param number: Number of frames per second to visualize.
        :type number: int
        """
        self.fps_counter_text.string = 'FPS: {}'.format(number)

    def set_mode(self, mode=None):
        """Set the current game mode on the game mode widget.

        :param number: The game mode: None in case of default
        :type number: :enum:`context.Context.GameMode`
        """
        self.game_mode_text.string = '{}'.format(mode.value)

    def set_clock(self, hour, minute):
        """Set the time in clock widget.

        :param hour: Hour.
        :type hour: int

        :param minute: Minute.
        :type minute: int
        """
        self.clock_text.string = '{h:02d}:{m:02d}'.format(h=hour, m=minute)

    def render(self):
        """Render the user interface."""
        self.scene.render(self.camera)


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
        context.ui.health_bar.value = evt.new / actor.resource.data['tot_hp']


from ui.item import Item
from ui import UI as Layout
from ui.item import Anchor


class AvatarItem(Item):

    def __init__(self, scene, texture, **kwargs):
        super().__init__(**kwargs)
        self.props = QuadProps()
        self.props.texture = texture
        self.quad = Quad(0, 0)
        self.obj = scene.add_quad(self.quad, self.props)

    def update(self):
        self.obj.position.x = self.position.x
        self.obj.position.y = self.position.y
        self.quad.right = self.width
        self.quad.bottom = self.height


class GameUI:
    """User interface.

    This class encapsulates the user interface creation and management.
    """

    def __init__(self, resource, width, height, player_data):
        """Constructor.

        :param resource: The UI resource.
        :type resource: :class:`loaders.Resource`

        :param width: UI width in pixels.
        :type width: int

        :param height: UI height in pixels.
        :type height: int

        :param player_data: Player resource.
        :type player_ddata: :class:`loaders.Resource`
        """
        self.w = width
        self.h = height
        self.scene = Scene()
        self.camera = OrthographicCamera(
            -self.w / 2,  # left
            +self.w / 2,  # right
            +self.h / 2,  # top
            -self.h / 2,  # bottom
            0,            # near
            1)            # far

        texture = Texture.from_image(
            player_data['avatar_res'][player_data['avatar']],
            Texture.TextureType.texture_rectangle)

        self.ui = Layout(width, height)
        self.ui.add_child(
            'avatar',
            AvatarItem(
                self.scene,
                texture,
                anchor=Anchor(
                    left='parent.left',
                    top='parent.top'),
                width=player_data['avatar_res'].data['width'],
                height=player_data['avatar_res'].data['height']))

        self.ui.bind_item()

    def update(self):
        self.ui.update()
