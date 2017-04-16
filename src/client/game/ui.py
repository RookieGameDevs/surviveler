from events import subscriber
from game.events import ActorStatusChange
from game.events import TimeUpdate
from renderlib.camera import OrthographicCamera
from renderlib.quad import Quad
from renderlib.quad import QuadProps
from renderlib.scene import Scene
from renderlib.text import Text
from renderlib.text import TextProps
from renderlib.texture import Texture
from renderlib.core import RenderTarget
from ui import UI as Layout
from ui.item import Anchor
from ui.item import Item
from ui.item import Margin
import logging

LOG = logging.getLogger(__name__)


@subscriber(TimeUpdate)
def update_time(evt):
    """Updates the UI clock."""
    evt.context.ui.set_clock(evt.hour, evt.minute)


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
        context.ui.set_health(evt.new / actor.resource.data['tot_hp'])


class ImageItem(Item):

    def __init__(self, scene, image, borders=None, **kwargs):
        super().__init__(**kwargs)
        self.props = QuadProps()
        self.props.texture = Texture.from_image(
            image,
            Texture.TextureType.texture_rectangle)
        if borders:
            for border, value in borders.items():
                if border in {'left', 'top', 'right', 'bottom'}:
                    setattr(self.props.borders, border, value)
        self.quad = Quad(0, 0)
        self.obj = scene.add_quad(self.quad, self.props)

    def update(self):
        self.quad.width = self.width
        self.quad.height = self.height
        self.obj.position.x = self.position.x
        self.obj.position.y = self.position.y


class TextItem(Item):

    def __init__(self, scene, font, string='', **kwargs):
        super().__init__(width=0, height=0, **kwargs)
        self.props = TextProps()
        self.text = Text(font, string)
        self.obj = scene.add_text(self.text, self.props)
        self._string = string

    @property
    def string(self):
        return self._string

    @string.setter
    def string(self, s):
        self._string = self.text.string = s

    def update(self):
        self.obj.position.x = self.position.x
        self.obj.position.y = self.position.y

    def compute_width(self):
        return self.text.width

    def compute_height(self):
        return self.text.height


class HealthbarItem(Item):

    def __init__(self, scene, resource, **kwargs):
        super().__init__(**kwargs)

        self._value = 1.0

        left, right, top, bottom = resource.data['borders']
        borders = {
            'left': left,
            'right': right,
            'top': top,
            'bottom': bottom,
        }

        self.background = ImageItem(
            scene,
            resource['bg_texture'],
            borders,
            anchor=Anchor.fill())
        self.background.obj.position.z = -0.5

        self.foreground = ImageItem(
            scene,
            resource['fg_texture'],
            borders,
            anchor=Anchor(
                top='parent.top',
                bottom='parent.bottom',
                left='parent.left'),
            width=0)

        self.add_child('healthbar-bg', self.background)
        self.add_child('healthbar-fg', self.foreground)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

    def update(self):
        self.foreground.width = self.width * self._value


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

        self.avatar = ImageItem(
            self.scene,
            player_data['avatar_res'][player_data['avatar']],
            anchor=Anchor(
                left='parent.left',
                top='parent.top'),
            margin=Margin(
                left=5,
                top=5),
            width=player_data['avatar_res'].data['width'],
            height=player_data['avatar_res'].data['height'])

        self.healthbar = HealthbarItem(
            self.scene,
            resource['health_bar'],
            anchor=Anchor(
                left='avatar.left',
                right='avatar.right',
                top='avatar.bottom'),
            margin=Margin(
                top=5),
            height=resource['health_bar'].data['height'])

        self.clock = TextItem(
            self.scene,
            resource['font'].get_size(16),
            '--:--',
            anchor=Anchor(
                hcenter='parent.hcenter',
                top='parent.top'),
            margin=Margin(
                top=5))

        self.fps_counter = TextItem(
            self.scene,
            resource['font'].get_size(16),
            'FPS: n/a',
            anchor=Anchor(
                left='parent.right',
                top='parent.top'),
            margin=Margin(
                top=5,
                left=-100))

        self.ui = Layout(width, height)
        self.ui.add_child('avatar', self.avatar)
        self.ui.add_child('healthbar', self.healthbar)
        self.ui.add_child('clock', self.clock)
        self.ui.add_child('fps_counter', self.fps_counter)
        self.ui.bind_item()

    def update(self):
        self.ui.update()

        # transform each item's graphical object
        for item in self.ui.traverse():
            obj = getattr(item, 'obj', None)
            if obj:
                item.obj.position.x = item.position.x - self.w / 2
                item.obj.position.y = self.h / 2 - item.position.y

    def render(self):
        self.scene.render(RenderTarget.overlay, self.camera)

    def set_fps(self, number):
        """Set the current frame rate in FPS widget.

        :param number: Number of frames per second to visualize.
        :type number: int
        """
        self.fps_counter.string = 'FPS: {}'.format(number)

    def set_clock(self, hour, minute):
        """Set the time in clock widget.

        :param hour: Hour.
        :type hour: int

        :param minute: Minute.
        :type minute: int
        """
        self.clock.string = '{h:02d}:{m:02d}'.format(h=hour, m=minute)

    def set_health(self, value):
        """Set the value in health bar widget.

        :param value: Health as normalized value in [0, 1] range.
        :type value: float
        """
        self.healthbar.value = value
