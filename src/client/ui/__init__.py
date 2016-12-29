"""The user interface package"""

from .item.root import RootItem
from enum import Enum


class EventType(Enum):
    """Enum of the various event types handled by the User Interface.
    """
    mouse_click = 'mouse_click'
    mouse_move = 'mouse_move'
    key_press = 'key_press'


class UI:
    """User interface class.
    """
    def __init__(self, width, height):
        """Constructor.

        :param width: The width of the UI
        :type width: :class:`int`

        :param height: The height of the UI
        :type height: :class:`int`
        """
        self._root = RootItem(width, height)

    @property
    def root(self):
        """Property containing the root item of the UI.
        """
        return self._root

    def add_child(self, *args, **kwargs):
        """Forward the add_child call as it is to the root item.
        """
        return self._root.add_child(*args, **kwargs)

    def bind_item(self):
        """Forward the bind_item call as it is to the root item.
        """
        return self._root.bind_item()

    def dispatch(self, event_type, pos=None, payload=None):
        """Traverses the item tree and dispatches the event properly.

        :param event_type: The event type
        :type event_type: :class:`EventType`

        :param pos: The position of the event (optional)
        :type pos: :class:`.util.point.Point`

        :param payload: The payload of the event
        :type payload: :class:`dict`

        :returns: True if the event was handled, False otherwise.
        :rtype: :class:`bool`
        """
        stop_propagation = False
        for item in self._root.traverse(listen_to=event_type, pos=pos):
            stop_propagation = item.handle(event_type, payload)
            if stop_propagation:
                break
        return stop_propagation

    def mouse_click_event_handler(self):
        """Returns the mouse click event handler function.

        To dispatch properly the events to the user interface, the caller needs
        to get a event handler and call it with the appropriate arguments.

        The mouse click event handler accepts three arguments: the button, the
        state and the pos.

        :returns: The mouse click event handler
        :rtype: :class:`function`
        """
        ET = EventType
        return (
            lambda button, state, pos:
            self.dispatch(
                ET.mouse_click,
                pos=pos,
                payload={'button': button, 'state': state})
        )

    def mouse_move_event_handler(self):
        """Returns the mouse move event handler function.

        To dispatch properly the events to the user interface, the caller needs
        to get a event handler and call it with the appropriate arguments.

        The mouse move event handler accepts only one argument: the cursor
        position.

        :returns: The mouse move event handler
        :rtype: :class:`function`
        """
        ET = EventType
        return (
            lambda pos:
            self.dispatch(ET.mouse_move, pos=pos)
        )

    def key_press_event_handler(self):
        """Returns the key press event handler function.

        To dispatch properly the events to the user interface, the caller needs
        to get a event handler and call it with the appropriate arguments.

        The key press event handler accepts two arguments: the pressed key and
        the state.

        :returns: The mouse move event handler
        :rtype: :class:`function`
        """
        ET = EventType
        return (
            lambda key, state:
            self.dispatch(ET.key_press, key=key, payload={'state': state})
        )
