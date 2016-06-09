from datetime import datetime
from events import subscriber
from game.events import CharacterJoin
from game.events import CharacterLeave
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
        self.camera = OrthoCamera(0, self.w, 0, self.h, 1)

        self.log_line_height = 18
        self.log_height = 0
        self.log_color = Vec(0.4, 0.4, 0.4)
        self.log_font = Font(resource['font'], 14)
        self.log_shader = resource['shader']
        self.log_node = self.scene.root.add_child(SceneNode())

        self.fps_counter_node = self.scene.root.add_child(TextNode(
            self.log_font,
            self.log_shader,
            'FPS',
            self.log_color))

        self.fps_counter_node.transform.translate(
            Vec(self.w - self.w * 0.1, 0, 0))

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

        txt.transform.identity()
        txt.transform.translate(Vec(0, self.log_height, 0))
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
