from enum import IntEnum
from enum import unique
from events import send_event
from game.events import EntityIdle
from game.events import EntityMove
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


def gamestate_entities(gamestate):
    """Returns the entities available in the gamestate.

    :param gamestate: the gamestate.
    :type gamestate: dict

    :return: server id, entity
    :rtype: tuple
    """
    # TODO: do we need more parsing here?
    for srv_id, e in gamestate.get(MessageField.entities, {}).items():
        yield srv_id, e


@processor
def update_user_position(gamestate):
    """Creates and triggers the PlayerPositionUpdated event.

    :param gamestate: the gamestate
    :type gamestate: dict
    """
    for srv_id, entity in gamestate_entities(gamestate):
        # Update the position of every idle entity
        if entity.get(MessageField.action_type, ActionType.idle) == ActionType.idle:
            x, y = entity[MessageField.x_pos], entity[MessageField.y_pos]
            evt = EntityIdle(srv_id, x, y)
            send_event(evt)


@processor
def player_move_action(gamestate):
    """Checks if the player is actually doing any move action and send the
    proper event.

    :param gamestate: the gamestate
    :type gamestate: dict
    """
    for srv_id, entity in gamestate_entities(gamestate):
        if entity.get(MessageField.action_type, None) == ActionType.move:
            action = entity[MessageField.action]
            send_event(EntityMove(
                srv_id,
                position=(
                    entity[MessageField.x_pos], entity[MessageField.y_pos]),
                destination=(
                    action[MessageField.x_pos], action[MessageField.y_pos]),
                speed=action[MessageField.speed]))
