"""Button item module"""

from . import Item
from . import Anchor
from . import Margin
from .rect import Rect
from .text import Text


class Button(Item):
    """Button item class.

    A simple button with colored background a text.
    """

    def __init__(self, **kwargs):
        """Constructor.

        FIXME: find a proper way to define fonts.

        Keyword Arguments:
            * position (:class:`..util.point.Point`): The item position relative to
                the parent
            * width (:class:`int`): The item width
            * height (:class:`int`): The item height
            * anchor (:class:`.Anchor`): The item anchor override
            * margin (:class:`.Margin`): The item margin override
            * on (:class:`dict`): The dictionary containing the listeners
            * background (:class:`tuple`): The background color
            * color (:class:`tuple`): The text color
            * font (:class:`str`): The text font
            * text (:class:`str`): The text
        """
        background = kwargs.pop('background', None)
        font = kwargs.pop('font', None)
        color = kwargs.pop('color', None)
        text = kwargs.pop('text', None)
        super().__init__(**kwargs)

        self.add_child(
            'background',
            Rect(background=background, anchor=Anchor.fill()))

        self.add_child(
            'label',
            Text(
                font=font, color=color, text=text, anchor=Anchor.fill(),
                margin=Margin.symmetric(10)))

    def update(self, dt):
        """Button update method.

        NOTE: this is a noop

        :param dt: The time delta since last update (in seconds)
        :type dt: :class:`float`
        """
        pass
