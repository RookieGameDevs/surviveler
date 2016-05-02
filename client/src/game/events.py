from abc import ABC
from collections import defaultdict


__SUBSCRIBED = defaultdict(list)


def subscriber(event):
    """Decorator for event handlers.

    :param event: the event to be handled
    :type event: :class:`Event`
    """
    # TODO: check that event is actually an Event instance
    def wrap(f):
        __SUBSCRIBED[event].append(f)
        return f
    return wrap


def send_event(event):
    for subscriber in __SUBSCRIBED[type(event)]:
        subscriber(event)


class Event(ABC):
    """Abstract base class for all the event classes.
    """
    pass


class PlayerPositionUpdated(Event):
    """Temporary event.

    This event is here just to test the whole event handling machine.
    """
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __str__(self):
        return '<PlayerPositionUpdate({}, {})>'.format(self.x, self.y)
