from datetime import datetime
from events import subscriber
from game.events import CharacterJoin
from matlib import Mat4
from matlib import Vec3
from renderer import Font
from renderer import OrthoCamera
from renderer import Scene
from renderer import SceneNode
from renderer import Shader
from renderer import TextNode


class UI:
    """User interface."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.w = renderer.width
        self.h = renderer.height
        self.scene = Scene()

        aspect = self.h / float(self.w)
        self.camera = OrthoCamera(
            0,
            self.w,
            0,
            aspect * self.h,
            1)

        self.log_line_height = 18
        self.log_height = 0
        self.log_color = Vec3(0.4, 0.4, 0.4)
        self.log_font = Font('data/fonts/Monaco-Linux.ttf', 14)
        self.log_shader = Shader.from_glsl(
            'data/shaders/text.vert',
            'data/shaders/text.frag')
        self.log_node = self.scene.root.add_child(SceneNode())

        self.fps_counter_node = self.scene.root.add_child(TextNode(
            self.log_font,
            self.log_shader,
            'FPS',
            self.log_color))
        self.fps_counter_node.transform = Mat4.trans(Vec3(
            self.w - self.w * 0.1, 0, 0))

    def set_fps(self, number):
        """Set the current frame rate in FPS widget."""
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
        txt.transform = Mat4.trans(Vec3(0, self.log_height, 0))
        self.log_height += self.log_line_height

    def render(self):
        """Render the user interface."""
        self.scene.render(self.renderer, self.camera)


@subscriber(CharacterJoin)
def log_join(evt):
    """Logs the name and ID of the joined character to UI console."""
    evt.context.ui.log('[{}] {} joined with ID {}'.format(
        datetime.now().time().replace(microsecond=0).isoformat(),
        evt.name,
        evt.srv_id))
