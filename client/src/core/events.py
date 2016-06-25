from enum import Enum
from enum import unique
from events import Event


class MouseClickEvent(Event):
    """Mouse click event."""

    @unique
    class Button(Enum):
        """Enumeration of mouse buttons."""
        left = 'Left'
        right = 'Right'
        unknown = 'Unknown'

    @unique
    class State(Enum):
        """Enumeration of button states."""
        up = 'Up'
        down = 'Down'

    def __init__(self, x, y, button, state):
        """Constructor.

        :param x: X coordinate of the click.
        :type x: int

        :param y: Y coordinate of the click.
        :type y: int

        :param button: Button clicked.
        :type button: enum of :class:`core.events.MouseClickEvent.Button`

        :param state: Button state.
        :type state: enum of :class:`core.events.MouseClickEvent.State`
        """
        self.x = x
        self.y = y
        self.button = button
        self.state = state

    def __str__(self):
        return '<MouseClickEvent({}, {}, {}, {})>'.format(
            self.x,
            self.y,
            self.button,
            self.state)


class MouseMoveEvent(Event):
    """Mouse move event."""

    def __init__(self, x, y):
        """Constructor.

        :param x: X coordinate of the click.
        :type x: int

        :param y: Y coordinate of the click.
        :type y: int
        """
        self.x = x
        self.y = y

    def __str__(self):
        return '<MouseMoveEvent({}, {})>'.format(self.x, self.y)


class KeyPressEvent(Event):
    """Key press event."""

    @unique
    class State(Enum):
        """Enumeration of key states."""
        up = 'Up'
        down = 'Down'

    def __init__(self, key):
        """Constructor.

        :param key:
        :type key:
        """
        self.key = key

    def __str__(self):
        return '<KeyPressEvent({})>'.format(self.key)
