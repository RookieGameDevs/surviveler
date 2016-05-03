from game.events import PlayerActionMove
from game.events import PlayerPositionUpdated
from game.events import send_event
from network import MessageField
from network import MessageType
import logging


LOG = logging.getLogger(__name__)

__PROCESSORS = []


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
    action = gamestate.get(MessageField.action, None)
    if action and action.get(MessageField.action_type, None) == MessageType.move:
        send_event(PlayerActionMove(
            position=(
                gamestate[MessageField.x_pos], gamestate[MessageField.y_pos]),
            destination=(
                action[MessageField.x_pos], action[MessageField.y_pos]),
            current_tstamp=gamestate[MessageField.timestamp],
            target_tstamp=action[MessageField.timestamp]))
