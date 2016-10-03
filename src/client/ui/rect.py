"""Rect item module"""

from .item import Item


class Rect(Item):
    """Rect item class.

    Concrete implementation of items representing rectangles.
    """

    def __init__(
            self,
            parent=None, position=None, size=None, anchor=None, margin=None,
            color=None):
        """Constructor.

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

        :param color: The background color
        :type color: :class:`tuple`
        """
        super().__init__(parent, position, size, anchor, margin)
        self._color = color

    @property
    def color(self):
        """Returns the rect color.

        :returns: The rect color
        :rtype: :class:`tuple`
        """
        return self._color

    @color.setter
    def color(self, color):
        """Sets the color for the rect.

        :param color: The new color
        :type color: :class:`tuple`
        """
        self._color = color

    def update(self, dt):
        """Rect update method.

        NOTE: this is a noop

        :param dt: The time delta since last update (in seconds)
        :type dt: :class:`float`
        """
        pass
