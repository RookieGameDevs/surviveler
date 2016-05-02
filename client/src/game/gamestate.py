from game.events import PlayerPositionUpdated
from game.events import send_event
from network import MessageField
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
