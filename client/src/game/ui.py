from datetime import datetime
from events import subscriber
from game.events import CharacterJoin
from game.events import CharacterLeave
from math import pi
from matlib import Vec
from renderer import Font
from renderer import OrthoCamera
from renderer import Scene
from renderer import SceneNode
from renderer import TextNode


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

        self.log_line_height = 18
        self.log_height = 0
        self.log_color = Vec(0.7, 0.7, 0.7)
        self.log_font = Font(resource['font'], 14)
        self.log_shader = resource['shader']
        self.log_node = self.scene.root.add_child(SceneNode())

        self.fps_counter_node = self.scene.root.add_child(TextNode(
            self.log_font,
            self.log_shader,
            'FPS',
            self.log_color))

        self.transform(self.fps_counter_node, self.w * 0.90, 0)

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
