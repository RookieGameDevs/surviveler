from matlib import Vec
from renderer import RenderOp
from renderer.mesh import Rect
from renderer.scene import SceneNode


class TextNode(SceneNode):
    """A node for rendering text."""

    def __init__(self, font, shader, text, color=Vec(1, 1, 1, 1)):
        """Constructor.

        :param font: Font to use.
        :type font: :class:`renderer.Font`

        :param shader: Shader to use.
        :type shader: :class:`renderer.Shader`

        :param text: Initial text string to render, must not be empty.
        :type text: tr

        :param color: Text color.
        :type color: :class:`matlib.Vec`
        """
        super(TextNode, self).__init__()
        self.font = font

        # initialize shader parameters
        self._text = None
        self.text = text
        self.shader = shader
        self.color = color

    @property
    def text(self):
        """Text string currently rendered.

        :returns: Text
        :rtype: str
        """
        return self._text

    @text.setter
    def text(self, text):
        """Sets the text string to render.

        :param text: New text.
        :type text: str
        """
        if self._text != text:
            self._text = text
            self._texture = self.font.render_to_texture(text)
            self._rect = Rect(self._texture.width, self._texture.height, False)

    @property
    def width(self):
        """Width of the text node's underlying texture."""
        return self._texture.width

    @property
    def height(self):
        """Height of the text node's underlying texture."""
        return self._texture.height

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        """Color of the text node."""
        self._color = color

    def render(self, ctx, transform):
        params = {
            'color': self._color,
            'width': self.width,
            'height': self.height,
            'tex': self._texture,
            'transform': transform,
            'modelview': ctx.modelview,
            'projection': ctx.projection,
        }

        v = (ctx.view * transform) * Vec(0, 0, 0, 1)

        ctx.renderer.add_render_op(RenderOp(
            v.z, self.shader, params, self._rect, textures=[self._texture]))
