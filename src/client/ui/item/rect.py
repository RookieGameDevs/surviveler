"""Rect item module"""

from . import Item


class Rect(Item):
    """Rect item class.

    Concrete implementation of items representing rectangles.
    """

    def __init__(self, parent, **kwargs):
        """Constructor.

        :param parent: The parent item
        :type parent: :class:`ui.item.Item`

        Keyword Arguments:
            * position (:class:`..util.point.Point`): The item position relative to
                the parent
            * width (:class:`int`): The item width
            * height (:class:`int`): The item height
            * anchor (:class:`.Anchor`): The item anchor override
            * margin (:class:`.Margin`): The item margin override
            * color (:class:`tuple`): The background color
        """
        color = kwargs.pop('color', None)
        super().__init__(parent, **kwargs)
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
