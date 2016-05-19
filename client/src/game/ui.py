from renderer import Font
from renderer import TextNode
from renderer import Shader
from renderer import Scene
from matlib import Vec3


class UI(Scene):
    """User interface."""

    def __init__(self):
        super(UI, self).__init__()

        text_shader = Shader.from_glsl(
            'data/shaders/text.vert',
            'data/shaders/text.frag')

        font = Font('data/fonts/Monaco-Linux.ttf', 14)
        text = TextNode(font, text_shader, 'Surviveler', color=Vec3(0.3, 0.3, 0.3))
        self.root.add_child(text)
