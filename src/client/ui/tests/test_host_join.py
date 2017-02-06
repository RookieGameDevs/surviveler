from ui import UI
from ui.item import Anchor
from ui.item.button import Button
from ui.item.rect import Rect
from ui.item.text import Text
from ui.util.point import Point
import pytest


@pytest.fixture
def host_join_menu():
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


def test_host_join__creation(ui_instance, host_join_menu):
    ui_instance.add_child('host_join', host_join_menu)
    ui_instance.bind_item()


def test_host_join__click_on_quit_button(ui_instance, host_join_menu):
    ui_instance.add_child('host_join', host_join_menu)
    ui_instance.bind_item()

    click = ui_instance.mouse_click_event_handler()
    click('left', 'up', Point(75, 150))
    # TODO: click on the quit button
    # TODO: proper event is triggered
    pass


def test_host_join__click_on_join_button__no_host(ui_instance, host_join_menu):
    ui_instance.add_child('host_join', host_join_menu)
    ui_instance.bind_item()
    # TODO: click on the join button
    # TODO: nothing happens
    pass


def test_host_join__keyboard_input__no_focus(ui_instance, host_join_menu):
    ui_instance.add_child('host_join', host_join_menu)
    ui_instance.bind_item()
    # TODO: write some text without clicking on the input field
    # TODO: nothing happens
    pass


def test_host_join__keyboard_input__focus(ui_instance, host_join_menu):
    ui_instance.add_child('host_join', host_join_menu)
    ui_instance.bind_item()
    # TODO: click on the input field
    # TODO: the input field has focus
    # TODO: write the hostname
    # TODO: the text into the field is changed accordingly
    pass


def test_host_join__click_on_join_button(ui_instance, host_join_menu):
    ui_instance.add_child('host_join', host_join_menu)
    ui_instance.bind_item()
    # TODO: click on the input field
    # TODO: the input field has focus
    # TODO: write the hostname
    # TODO: the text into the field is changed accordingly
    # TODO: click on the join Button
    # TODO: the proper event is triggered
    pass
