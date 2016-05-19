from matlib import Vec3
from renderer import Font
from renderer import OrthoCamera
from renderer import Scene
from renderer import Shader
from renderer import TextNode


class UI:
    """User interface."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.scene = Scene()

        aspect = renderer.height / float(renderer.width)
        self.camera = OrthoCamera(
            0,
            self.renderer.width,
            0,
            aspect * self.renderer.height,
            1)

        text_shader = Shader.from_glsl(
            'data/shaders/text.vert',
            'data/shaders/text.frag')

        font = Font('data/fonts/Monaco-Linux.ttf', 14)
        text = TextNode(font, text_shader, 'Surviveler', color=Vec3(0.3, 0.3, 0.3))
        self.scene.root.add_child(text)

    def render(self):
        """Render the user interface."""
        self.scene.render(self.renderer, self.camera)
