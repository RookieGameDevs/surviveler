from ui import UI
from ui.item import Anchor
from ui.item.button import Button
from ui.item.rect import Rect
from ui.item.root import RootItem
from ui.item.text import Text
import pytest


@pytest.fixture
def host_join_item_factory():
    return Rect(
        width=300,
        height=100,
        anchor=Anchor.center(),
        children=dict(
            host=Rect(
                anchor=Anchor(
                    top='parent.top',
                    bottom='parent.vcenter',
                    left='parent.left',
                    right='parent.right',
                ),
                children=dict(
                    host_input=Text(
                        anchor=Anchor(
                            left='parent.left',
                            top='parent.top',
                            bottom='parent.bottom',
                        ),
                        width=200,
                    ),
                    host_join_button=Button(
                        anchor=Anchor(
                            right='parent.right',
                            top='parent.top',
                            bottom='parent.bottom',
                        ),
                        width=100,
                        color=(0, 0, 0),
                        font=None,  # FIXME: we need fonts
                        text='Join',
                    ),
                ),
            ),
            quit_button=Button(
                anchor=Anchor(
                    right='parent.right',
                    left='parent.left',
                    top='parent.vcenter',
                    bottom='parent.bottom',
                ),
                color=(0, 0, 0),
                font=None,  # FIXME: we need fonts
                text='Quit to desktop',
            ),
        ),
    )


@pytest.fixture
def ui_instance():
    return UI(500, 500)


def test_ui(ui_instance):
    assert isinstance(ui_instance._root, RootItem)


def test_host_join(ui_instance, host_join_item_factory):
    ui_instance.add_child('host_join', host_join_item_factory)
    ui_instance.bind_item()
