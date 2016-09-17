"""Button item module"""

from .item import Item
from .rect import Rect
from .text import Text


class Button(Item):
    """Button item class.

    A simple button with colored background a text.
    """

    def __init__(
            self,
            parent=None, position=None, size=None, anchor=None, margin=None,
            background=None, font=None, color=None, text=''):
        """Constructor.

        FIXME: find a proper way to define fonts.

        :param parent: The parent item
        :type parent: :class:`ui.item.Item`

        :param position: The item position relative to the parent
        :type position: :class:`tuple`

        :param size: The position width and height
        :type size: :class:`tuple`

        :param anchor: The item anchor override
        :type anchor: :class:`ui.item.Anchor`

        :param margin: The item margin override
        :type margin: :class:`ui.item.Margin`

        :param background: The background color
        :type background: :class:`tuple`

        :param font: The text font
        :type font: :class:`str`

        :param color: The text color
        :type color: :class:`tuple`

        :param text: The text
        :type text: :class:`str`
        """
        super().__init__(parent, position, size, anchor, margin)

        self.add_child(
            'background',
            Rect(self, background=background),
            background='color')

        self.add_child(
            'label',
            Text(self, font, color, text),
            font='font', color='color', text='text')

    def update(self, dt):
        """Button update method.

        NOTE: this is a noop

        :param dt: The time delta since last update (in seconds)
        :type dt: :class:`float`
        """
        pass
