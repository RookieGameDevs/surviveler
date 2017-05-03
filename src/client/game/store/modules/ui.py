"""UI store module."""

from revived.action import action
from revived.action import ActionType as BaseActionType
from revived.reducer import Module
from revived.store import ActionType as StoreActionType


class ActionType(BaseActionType):
    TOGGLE_TERMINAL = 'toggle_terminal'


@action(ActionType.TOGGLE_TERMINAL)
def toggle_terminal(visible):
    return {'visible': visible}


reducer = Module()


@reducer.reducer(StoreActionType.INIT)
def init(prev, action):
    return {
        'terminal': {'is_visible': False}
    }


@reducer.reducer(ActionType.TOGGLE_TERMINAL)
def toggle_terminal_reducer(prev, action):
    terminal = prev.get('terminal', {})
    return dict(
        prev,
        terminal=dict(
            terminal,
            is_visible=action['visible']))
