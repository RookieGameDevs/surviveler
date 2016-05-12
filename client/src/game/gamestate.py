from enum import IntEnum
from enum import unique
from events import send_event
from game.events import PlayerActionMove
from game.events import PlayerPositionUpdated
from network import MessageField
import logging


LOG = logging.getLogger(__name__)

__PROCESSORS = []


@unique
class ActionType(IntEnum):
    """Enum of the various possible ActionType"""
    idle = 0
    move = 1


def processor(f):
    """Decorator for gamestate processors.
    """
    __PROCESSORS.append(f)
    return f


def process_gamestate(gamestate):
    """Calls all the registered processors passing the gamestate as parameter.
    """
    for proc in __PROCESSORS:
        proc(gamestate)


@processor
def update_user_position(gamestate):
    """Creates and triggers the PlayerPositionUpdated event.

    :param gamestate: the gamestate
    :type gamestate: dict
    """
    if gamestate.get(MessageField.action_type, ActionType.idle) == ActionType.idle:
        # NOTE: Update the position in this way only when the item is in "idle"
        x, y = gamestate[MessageField.x_pos], gamestate[MessageField.y_pos]
        evt = PlayerPositionUpdated(x, y)
        send_event(evt)


@processor
def player_move_action(gamestate):
    """Checks if the player is actually doing any move action and send the
    proper event.

    :param gamestate: the gamestate
    :type gamestate: dict
    """
    if gamestate.get(MessageField.action_type, None) == ActionType.move:
        action = gamestate[MessageField.action]
        send_event(PlayerActionMove(
            position=(
                gamestate[MessageField.x_pos], gamestate[MessageField.y_pos]),
            destination=(
                action[MessageField.x_pos], action[MessageField.y_pos]),
            speed=action[MessageField.speed]))
