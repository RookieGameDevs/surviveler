from renderer.scene import SceneNode
from renderer.mesh import Rect
from matlib import Vec


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

    def render(self, ctx, transform):
        params = {
            'transform': transform,
            'modelview': ctx.modelview,
            'projection': ctx.projection,
            'width': self._texture.width,
            'height': self._texture.height,
            'tex': self._texture,
            'color': self.color,
        }
        with self._texture.use(0):
            self.shader.use(params)
            self._rect.render(ctx.renderer)
