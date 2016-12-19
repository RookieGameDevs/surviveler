"""Text item module"""

from . import Item


class Text(Item):
    """Text item class.

    Concrete implementation of items representing texts.
    """

    def __init__(self, parent, **kwargs):
        """Constructor.

        FIXME: find a proper way to define fonts.

        :param parent: The parent item
        :type parent: :class:`ui.item.Item`

        Keyword Arguments:
            * position (:class:`..util.point.Point`): The item position relative to
                the parent
            * width (:class:`int`): The item width
            * height (:class:`int`): The item height
            * anchor (:class:`.Anchor`): The item anchor override
            * margin (:class:`.Margin`): The item margin override
            * on (:class:`dict`): The dictionary containing the listeners
            * color (:class:`tuple`): The background color
            * font (:class:`str`): The text font
            * text (:class:`str`): The text
        """
        font = kwargs.pop('font', None)
        color = kwargs.pop('color', None)
        text = kwargs.pop('text', '')
        super().__init__(parent, **kwargs)
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
