"""The user interface package"""

from .item.root import RootItem
from enum import Enum


class EventType(Enum):
    mouse_click = 'mouse_click'
    mouse_move = 'mouse_move'
    key_press = 'key_press'


class UI:
    def __init__(self, width, height):
        self._root = RootItem(width, height)

    @property
    def root(self):
        return self._root

    def dispatch(self, event_type, **payload):
        # TODO: Actually dispatch the event
        pass

    def mouse_click_event_handler(self):
        ET = EventType
        return (lambda button, state, pos:
            self.dispatch(ET.mouse_click, button=button, state=state, pos=pos))

    def mouse_move_event_handler(self):
        ET = EventType
        return lambda pos: self.dispatch(ET.mouse_click, pos=pos)

    def key_press_event_handler(self):
        ET = EventType
        return lambda key, state: self.dispatch(ET.mouse_click, key=key, state=state)
