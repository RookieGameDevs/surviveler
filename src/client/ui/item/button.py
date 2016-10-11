"""Button item module"""

from . import Item
from .. import Anchor
from .rect import Rect
from .text import Text


class Button(Item):
    """Button item class.

    A simple button with colored background a text.
    """

    def __init__(self, parent, **kwargs):
        """Constructor.

        FIXME: find a proper way to define fonts.

        :param parent: The parent item
        :type parent: :class:`ui.item.Item`

        Keyword Arguments:
            * position (:class:`..point.Point`): The item position relative to
                the parent
            * width (:class:`int`): The item width
            * height (:class:`int`): The item height
            * anchor (:class:`..Anchor`): The item anchor override
            * margin (:class:`..Margin`): The item margin override
            * background (:class:`tuple`): The background color
            * color (:class:`tuple`): The text color
            * font (:class:`str`): The text font
            * text (:class:`str`): The text
        """
        background = kwargs.pop('background', None)
        font = kwargs.pop('font', None)
        color = kwargs.pop('color', None)
        text = kwargs.pop('text', None)
        super().__init__(parent, **kwargs)

        self.add_child(
            'background',
            Rect(self, background=background, anchor=Anchor.fill()),
            background='color')

        self.add_child(
            'label',
            Text(self, font=font, color=color, text=text, anchor=Anchor.fill()),
            font='font', color='color', text='text')

    def update(self, dt):
        """Button update method.

        NOTE: this is a noop

        :param dt: The time delta since last update (in seconds)
        :type dt: :class:`float`
        """
        pass
