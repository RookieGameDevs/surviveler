from ui import Anchor
from ui import Margin
from ui.item import Item
from ui.item import ValidationError
from ui.item.root import RootItem
from ui.point import Point
import pytest


class Dummy(Item):

    def update(self, dt):
        pass


@pytest.fixture
def item_cls():
    return Dummy


@pytest.fixture
def parent_item():
    return RootItem(500, 500)


def test_item_is_abtract():
    with pytest.raises(TypeError):
        Item()


def test_item__with_redundant_width_height(item_cls, parent_item):
    # Explicit width and two horizontal anchor values
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                left='parent.left',
                right='parent.right',
                top='parent.top'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                left='parent.left',
                hcenter='parent.hcenter',
                top='parent.top'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                hcenter='parent.hcenter',
                right='parent.right',
                top='parent.top'),
            width=100, height=100)
    # Explicit height and two vertical anchor values
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                top='parent.top',
                bottom='parent.bottom',
                left='parent.left'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                top='parent.top',
                vcenter='parent.vcenter',
                left='parent.left'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                vcenter='parent.vcenter',
                bottom='parent.bottom',
                left='parent.left'),
            width=100, height=100)


def test_item__without_information(item_cls, parent_item):
    with pytest.raises(ValidationError):
        item_cls(parent_item)


def test_item__with_position_and_size(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(parent_item, position=Point(25, 25), width=30, height=30)
    parent_item.add_child('child', item)
    parent_item.bind_item()
    assert item.anchor == {
        AT.left: 25,
        AT.hcenter: 40,
        AT.right: 55,
        AT.top: 25,
        AT.vcenter: 40,
        AT.bottom: 55,
    }
    assert item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert item.position == Point(25, 25)
    assert item.width == 30
    assert item.height == 30


def test_item__sub_item_with_position_and_size(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(parent_item, position=Point(25, 25), width=30, height=30)
    parent_item.add_child('child', item)
    sub_item = item_cls(item, position=Point(25, 25), width=30, height=30)
    item.add_child('child', sub_item)
    parent_item.bind_item()
    assert sub_item.anchor == {
        AT.left: 50,
        AT.hcenter: 65,
        AT.right: 80,
        AT.top: 50,
        AT.vcenter: 65,
        AT.bottom: 80,
    }
    assert sub_item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert sub_item.position == Point(50, 50)
    assert sub_item.width == 30
    assert sub_item.height == 30


def test_item__with_anchor_fill(item_cls, parent_item):
    MT = Margin.MarginType
    item = item_cls(parent_item, anchor=Anchor.fill())
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == parent_item.anchor
    assert item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert item.position == parent_item.position
    assert item.width == parent_item.width
    assert item.height == parent_item.height


def test_item__with_cutom_anchor(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(
        parent_item,
        anchor=Anchor(
            top='parent.vcenter',
            bottom='parent.bottom',
            hcenter='parent.hcenter'),
        width=100)
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == {
        AT.left: 200,
        AT.hcenter: 250,
        AT.right: 300,
        AT.top: 250,
        AT.vcenter: 375,
        AT.bottom: 500,
    }
    assert item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert item.position == Point(200, 250)
    assert item.width == 100
    assert item.height == 250


def test_item__with_fill_anchor_and_symmetric_margin(item_cls, parent_item):
    MARGIN = 10
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(
        parent_item,
        anchor=Anchor.fill(),
        margin=Margin.symmetric(MARGIN))
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == {
        AT.left: parent_item.anchor[AT.left] + MARGIN,
        AT.hcenter: parent_item.anchor[AT.hcenter],
        AT.right: parent_item.anchor[AT.right] - MARGIN,
        AT.top: parent_item.anchor[AT.top] + MARGIN,
        AT.vcenter: parent_item.anchor[AT.vcenter],
        AT.bottom: parent_item.anchor[AT.bottom] - MARGIN,
    }
    assert item.margin == {
        MT.left: MARGIN,
        MT.right: MARGIN,
        MT.top: MARGIN,
        MT.bottom: MARGIN,
    }

    assert item.width == parent_item.width - 2 * MARGIN
    assert item.height == parent_item.height - 2 * MARGIN


def test_item__with_complex_anchor_and_margin(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.hcenter',
            top='parent.top',
            bottom='parent.hcenter'),
        margin=Margin(left=4, right=10, top=10, bottom=4))
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == {
        AT.left: 4,
        AT.hcenter: 122,
        AT.right: 240,
        AT.top: 10,
        AT.vcenter: 128,
        AT.bottom: 246,
    }
    assert item.margin == {
        MT.left: 4,
        MT.right: 10,
        MT.top: 10,
        MT.bottom: 4,
    }

    assert item.width == 236
    assert item.height == 236
