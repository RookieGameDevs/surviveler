from abc import ABC
from collections import defaultdict
from enum import Enum
from enum import unique


__SUBSCRIBED = defaultdict(list)


def subscriber(event):
    """Decorator for event handlers.

    :param event: the event to be handled
    :type event: :class:`Event`
    """
    def wrap(f):
        __SUBSCRIBED[event].append(f)
        return f
    return wrap


def send_event(event):
    """Emits the given event.

    Calls all the event handlers subscribed to the specified event.

    :param event: The event to be emitted.
    :type event: :class:`game.events.Event`
    """
    for subscriber in __SUBSCRIBED[type(event)]:
        subscriber(event)


class Event(ABC):
    """Abstract base class for all the event classes.
    """
    pass


class PlayerPositionUpdated(Event):
    """Player position updated.

    Event emitted when the position of the Player changed.
    """
    def __init__(self, x, y):
        """Constructor.

        :param x: The position on x-axis.
        :type x: float

        :param y: The position on y-axis.
        :type y: float
        """
        self.x, self.y = x, y

    def __str__(self):
        return '<PlayerPositionUpdated({}, {})>'.format(self.x, self.y)


class PlayerActionMove(Event):
    """Receved move action.

    Event emitted whenever the player is subject to a move action.

    :param action: Move action payload.
    :type action: dict
    """
    def __init__(self, current_position, destination, current_tstamp, target_tstamp):
        self.current_position = current_position
        self.destination = destination
        self.current_tstamp = current_tstamp
        self.target_tstamp = target_tstamp

    def __str__(self):
        return '<PlayerActionMove({}, {}, {}, {})>'.format(
            self.current_position, self.destination,
            self.current_tstamp, self.target_tstamp)


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
        :type button: enum of :class:`game.events.MouseClickEvent.Button`

        :param state: Button state.
        :type state: enum of :class:`game.events.MouseClickEvent.State`
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
