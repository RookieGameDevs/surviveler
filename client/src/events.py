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
    def __new__(cls, *args, **kwargs):
        """Injects the client instance in the event object."""
        # FIXME: cyclic import. Sounds like bad design.
        from client import Client
        inst = super(Event, cls).__new__(cls)
        inst.client = Client.get_instance()
        return inst
