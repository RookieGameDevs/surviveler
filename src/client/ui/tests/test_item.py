from ui import Anchor
from ui.item import Item
from ui.point import Point
from unittest.mock import Mock
import pytest


class Dummy(Item):

    def update(self, dt):
        pass


def assert_anchor_equal(a1, a2):
    assert set(a1) == set(a2)
    for k, v in a1.items():
        assert a2[k] == v


@pytest.fixture
def item_cls():
    return Dummy


@pytest.fixture
def parent_item():
    pos, (width, height) = Point(0, 0), (100, 100)
    parent = Mock()
    parent.position = pos
    parent.width = width
    parent.height = height
    parent.anchor = None
    parent.margin = None
    return parent


def test_item_is_abtract():
    with pytest.raises(TypeError):
        Item()


def test_item__without_information(item_cls, parent_item):
    item = item_cls(parent_item)
    assert item.anchor is None
    assert item.margin is None
    # Position is the same of the parent item
    assert item.position == parent_item.position
    # Size is 0
    assert item.width == 0
    assert item.height == 0


def test_item__with_position_and_size(item_cls, parent_item):
    item = item_cls(parent_item, position=Point(25, 25), width=25, height=25)
    assert item.anchor is None
    assert item.margin is None
    assert item.position == Point(25, 25)
    assert item.width == 25
    assert item.height == 25


def test_item__sub_item_with_position_and_size(item_cls, parent_item):
    item = item_cls(parent_item, position=Point(25, 25), width=25, height=25)
    sub_item = item_cls(item, position=Point(25, 25), width=25, height=25)
    assert sub_item.anchor is None
    assert sub_item.margin is None
    assert sub_item.position == Point(50, 50)
    assert sub_item.width == 25
    assert sub_item.height == 25


def test_item__with_anchor_fill(item_cls, parent_item):
    item = item_cls(parent_item, anchor=Anchor.fill())

    assert_anchor_equal(item.anchor, Anchor.fill())
    assert item.margin is None
    assert item.position == parent_item.position
    assert item.width == parent_item.width
    assert item.height == parent_item.height


def test_item__with_anchor_center(item_cls, parent_item):
    item = item_cls(parent_item, anchor=Anchor.center())

    assert_anchor_equal(item.anchor, Anchor.center())
    assert item.margin is None
    # TODO: check calculated relative position
    # TODO: check calculated absolute position
    # TODO: check calculated size


def test_item__with_anchor(item_cls, parent_item):
    # FIXME: add custom anchor
    item = item_cls(parent_item)
    # TODO: check anchor
    assert item.margin is None
    # TODO: check calculated relative position
    # TODO: check calculated absolute position
    # TODO: check calculated size


def test_item__with_anchor_and_margin(item_cls, parent_item):
    item = item_cls(parent_item)
    # TODO: check anchor
    # TODO: check margin
    # TODO: check calculated relative position
    # TODO: check calculated absolute position
    # TODO: check calculated size
