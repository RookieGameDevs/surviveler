"""Text item module"""

from .item import Item


class Text(Item):
    """Text item class.

    Concrete implementation of items representing texts.
    """

    def __init__(
            self,
            parent, position=None, size=None, anchor=None, margin=None,
            font=None, color=None, text=''):
        """Constructor.

        FIXME: find a proper way to define fonts.

        :param parent: The parent item
        :type parent: :class:`ui.item.Item`

        :param position: The item position relative to the parent
        :type position: :class:`tuple`

        :param size: The position width and height
        :type size: :class:`tuple`

        :param anchor: The item anchor override
        :type anchor: :class:`ui.Anchor`

        :param margin: The item margin override
        :type margin: :class:`ui.Margin`

        :param font: The text font
        :type font: :class:`str`

        :param color: The text color
        :type color: :class:`tuple`

        :param text: The text
        :type text: :class:`str`
        """
        super().__init__(parent, position, size, anchor, margin)
        self._font = font
        self._color = color
        self._text = text

    @property
    def font(self):
        """Returns the text font

        :returns: The text font
        :rtype: :class:`str`
        """

    @property
    def color(self):
        """Returns the text color.

        :returns: The text color
        :rtype: :class:`tuple`
        """
        return self._color

    @color.setter
    def color(self, color):
        """Sets the color for the text.

        :param color: The new color
        :type color: :class:`tuple`
        """
        self._color = color

    @property
    def text(self):
        """Returns the text.

        :returns: The text
        :rtype: :class:`str`
        """
        return self._text

    @text.setter
    def text(self, text):
        """Sets the text.

        :param text: The new text
        :type text: :class:`str`
        """
        self._text = text

    def update(self, dt):
        """Text update method.

        NOTE: this is a noop

        :param dt: The time delta since last update (in seconds)
        :type dt: :class:`float`
        """
        pass
