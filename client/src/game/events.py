from abc import ABC
from collections import defaultdict


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
        return '<PlayerPositionUpdate({}, {})>'.format(self.x, self.y)
