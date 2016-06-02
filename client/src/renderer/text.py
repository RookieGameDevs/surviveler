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

        # initialize shader parameters
        self.params = {
            k: shader.make_param(k) for k in
            [
                'transform',
                'modelview',
                'projection',
                'width',
                'height',
                'tex',
                'color'
            ]
        }
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
            self.params['width'].value = self.width
            self.params['height'].value = self.height
            self.params['tex'].value = self._texture

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
        self.params['color'].value = color

    def render(self, ctx, transform):
        self.params['transform'].value = transform
        self.params['modelview'].value = ctx.modelview
        self.params['projection'].value = ctx.projection

        with self._texture.use(0):
            self.shader.use(self.params.values())
            self._rect.render(ctx.renderer)
