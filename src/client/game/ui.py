from abc import abstractproperty
from context import Context
from core.events import MouseClickEvent
from events import send_event
from events import subscriber
from game.entities.actor import ActorType
from game.events import ActorStatusChange
from game.events import GameModeToggle
from game.events import TimeUpdate
from matlib.vec import Vec
from renderlib.camera import OrthographicCamera
from renderlib.core import RenderTarget
from renderlib.quad import Quad
from renderlib.quad import QuadProps
from renderlib.scene import Scene
from renderlib.text import Text
from renderlib.text import TextProps
from renderlib.texture import Texture
from ui import EventType
from ui import UI
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


class UIItem(Item):
    """Base class for surviveler user interface items.

    This class defines an interface for user interface items and exposes
    properties and methods which are needed for their integration with the
    rendering system.
    """

    @abstractproperty
    def objects(self):
        """List of scene objects which make up the item."""

    @abstractproperty
    def visible(self):
        """Item's visibility flag."""

    @visible.setter
    def visible(self, v):
        """Sets item's visibility."""

    @abstractproperty
    def z_index(self):
        """Item's Z index."""

    @z_index.setter
    def z_index(self, z):
        """Sets item's Z index."""


class ImageItem(UIItem):

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

    @property
    def objects(self):
        return [self.obj]

    @property
    def visible(self):
        return self.props.visible

    @visible.setter
    def visible(self, v):
        self.props.visible = v

    @property
    def z_index(self):
        return self.obj.position.z

    @z_index.setter
    def z_index(self, z):
        self.obj.position.z = z

    def update(self):
        self.quad.width = self.width
        self.quad.height = self.height


class TextItem(UIItem):

    def __init__(self, scene, font, string='', color=None, **kwargs):
        super().__init__(width=0, height=0, **kwargs)
        self.props = TextProps()
        if color:
            self.props.color = color
        self.text = Text(font, string)
        self.obj = scene.add_text(self.text, self.props)
        self._string = string

    @property
    def objects(self):
        return [self.obj]

    @property
    def visible(self):
        return self.props.visible

    @visible.setter
    def visible(self, v):
        self.props.visible = v

    @property
    def z_index(self):
        return self.obj.position.z

    @z_index.setter
    def z_index(self, z):
        self.obj.position.z = z

    @property
    def string(self):
        return self._string

    @string.setter
    def string(self, s):
        self._string = self.text.string = s

    def update(self):
        pass

    def compute_width(self):
        return self.text.width

    def compute_height(self):
        return self.text.height


class HealthbarItem(UIItem):

    def __init__(self, scene, **kwargs):
        resource = Context.get_instance().res_mgr.get('/ui/healthbar')

        super().__init__(**kwargs, height=resource.data['height'])

        self._value = 1.0
        self._visible = True
        self._z_index = 0

        self.background = ImageItem(
            scene,
            resource['background'],
            resource.data['borders'],
            anchor=Anchor.fill())

        self.foreground = ImageItem(
            scene,
            resource['foreground'],
            resource.data['borders'],
            anchor=Anchor(
                top='parent.top',
                bottom='parent.bottom',
                left='parent.left'),
            width=0)

        self.items = [self.background, self.foreground]
        self.z_offsets = [-0.1, 0]
        self.z_index = 0  # recompute absolute indices

        self.add_child('healthbar-bg', self.background)
        self.add_child('healthbar-fg', self.foreground)

    @property
    def objects(self):
        return []

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        for item in self.items:
            item.visible = v
        self._visible = v

    @property
    def z_index(self):
        return self._z_index

    @z_index.setter
    def z_index(self, z):
        for item, offset in zip(self.items, self.z_offsets):
            item.z_index = z + offset
        self._z_index = z

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

    def update(self):
        self.foreground.width = self.width * self._value


class ButtonItem(UIItem):

    def __init__(self, scene, icon, label, **kwargs):
        super().__init__(**kwargs)

        self._visible = True
        self._z_index = 0

        resource = Context.get_instance().res_mgr.get('/ui/button')

        self.frame = ImageItem(
            scene,
            resource[resource.data['states']['normal']['ref']],
            borders=resource.data['states']['normal']['borders'],
            anchor=Anchor.fill())

        self.icon = ImageItem(
            scene,
            icon,
            anchor=Anchor(
                vcenter='parent.vcenter',
                hcenter='parent.hcenter'),
            width=icon.width,
            height=icon.height)

        self.label = TextItem(
            scene,
            resource['font'].get_size(resource.data['text_size']),
            label,
            Vec(*resource.data['text_color']),
            anchor=Anchor(
                top='parent.top',
                left='parent.left'),
            margin=Margin(
                top=4,
                left=4))

        self.items = [self.frame, self.icon, self.label]
        self.z_offsets = [-0.2, -0.1, 0]
        self.z_index = 0  # recompute absolute indices

        self.add_child('button_frame', self.frame)
        self.add_child('button_icon', self.icon)
        self.add_child('button_label', self.label)

    @property
    def objects(self):
        return []

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        for item in self.items:
            item.visible = v
        self._visible = v

    @property
    def z_index(self):
        return self._z_index

    @z_index.setter
    def z_index(self, z):
        for item, offset in zip(self.items, self.z_offsets):
            item.z_index = z + offset
        self._z_index = z

    def update(self):
        pass


class ToolbarItem(UIItem):

    def __init__(self, scene, **kwargs):
        resource = Context.get_instance().res_mgr.get('/ui/toolbar')

        super().__init__(
            width=resource.data['width'],
            height=resource.data['height'],
            **kwargs)

        self._visible = True
        self._z_index = 0

        self.panel = ImageItem(
            scene,
            resource['panel'],
            borders=resource.data['borders'],
            anchor=Anchor.fill())

        self.items = [self.panel]
        self.z_offsets = [0]
        self.z_index = 0

        self.add_child('toolbar-panel', self.panel)

    @property
    def objects(self):
        return []

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        for item in self.items:
            item.visible = v
        self._visible = v

    @property
    def z_index(self):
        return self._z_index

    @z_index.setter
    def z_index(self, z):
        for item, offset in zip(self.items, self.z_offsets):
            item.z_index = z + offset
        self._z_index = z

    def update(self):
        pass


class UI(UI):
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
        super().__init__(width, height)

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
            anchor=Anchor(
                left='avatar.left',
                right='avatar.right',
                top='avatar.bottom'),
            margin=Margin(
                top=5))

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

        controls = {}
        if player_data['type'] == ActorType.engineer:
            # create toolbar
            toolbar = ToolbarItem(
                self.scene,
                anchor=Anchor(
                    hcenter='parent.hcenter',
                    bottom='parent.bottom'))
            toolbar.z_index = -1
            # prevent the click on the toolbar from being propagated further
            toolbar.on(EventType.mouse_click, lambda _: True)

            # add build mode toggle button
            build_button = ButtonItem(
                self.scene,
                resource['build_icon'],
                'B',
                anchor=Anchor(
                    left='parent.left',
                    vcenter='parent.vcenter'),
                margin=Margin(
                    left=10),
                width=52,
                height=52)
            build_button.on(EventType.mouse_click, self.handle_build_button_click)

            toolbar.add_child('build_button', build_button)
            controls['toolbar'] = toolbar

        self.add_child('avatar', self.avatar)
        self.add_child('healthbar', self.healthbar)
        self.add_child('clock', self.clock)
        self.add_child('fps_counter', self.fps_counter)

        for ref, item in controls.items():
            self.add_child(ref, item)

        self.bind_item()

    def update(self):
        super().update()

        # transform each item's graphical object
        for item in self.traverse():
            if isinstance(item, UIItem):
                for obj in item.objects:
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

    def handle_build_button_click(self, payload):
        btn, state = payload['button'], payload['state']
        if btn == MouseClickEvent.Button.left and state == MouseClickEvent.State.up:
            context = Context.get_instance()
            send_event(GameModeToggle(context.GameMode.building))
        return True
