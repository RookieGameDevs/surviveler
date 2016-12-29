from ui import EventType as ET
from ui import UI
from ui.item import Item
from ui.util.point import Point
import pytest


# TODO: put all the fixtures in a fixture module
class Dummy(Item):
    def __init__(self, *args, **kwargs):
        test_id = kwargs.pop('test_id', None)
        super().__init__(*args, **kwargs)
        if test_id:
            self.test_id = test_id

    def update(self, dt):
        pass


@pytest.fixture
def item_cls():
    return Dummy


@pytest.fixture
def ui_object():
    return UI(500, 500)


def test_ui__click_event__no_listeners(ui_object):
    click_event_handler = ui_object.mouse_click_event_handler()
    stop_propagation = click_event_handler('left', 'pressed', Point(100, 100))
    assert stop_propagation is False


def test_ui__click_event__single_listener(ui_object, item_cls):
    click_event_handler = ui_object.mouse_click_event_handler()
    item = item_cls(
        ui_object.root,
        position=Point(25, 25),
        width=30,
        height=30,
        on={ET.mouse_click: lambda payload: True})
    ui_object.root.add_child('child', item)
    ui_object.root.bind_item()

    assert click_event_handler('left', 'pressed', Point(30, 30)) is True
    assert click_event_handler('left', 'pressed', Point(20, 20)) is False


def test_ui__click_event__propagation(ui_object, item_cls):
    click_event_handler = ui_object.mouse_click_event_handler()

    items = []

    def handler1(payload):
        items.append('handler1')
        return False

    def handler2(payload):
        items.append('handler2')
        return True

    def handler3(payload):
        items.append('handler3')
        return False

    item1 = item_cls(
        ui_object.root,
        position=Point(25, 25),
        width=30,
        height=30,
        on={ET.mouse_click: handler1})

    item2 = item_cls(
        item1,
        position=Point(0, 0),
        width=20,
        height=20,
        on={ET.mouse_click: handler2})

    item3 = item_cls(
        item2,
        position=Point(0, 0),
        width=10,
        height=10,
        on={ET.mouse_click: handler3})

    ui_object.add_child('item1', item1)
    item1.add_child('item2', item2)
    item2.add_child('item3', item3)
    ui_object.root.bind_item()

    assert click_event_handler('left', 'pressed', Point(30, 30)) is True
    assert items == ['handler3', 'handler2']

    items[:] = []
    assert click_event_handler('left', 'pressed', Point(36, 36)) is True
    assert items == ['handler2']

    items[:] = []
    assert click_event_handler('left', 'pressed', Point(46, 46)) is False
    assert items == ['handler1']
