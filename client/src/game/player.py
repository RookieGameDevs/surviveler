from context import Context
from events import subscriber
from game import Character
from game.components import Movable
from game.events import PlayerJoin
from matlib import Vec
import logging


LOG = logging.getLogger(__name__)


class Player(Character):
    """Game entity representing the local player"""

    def update(self, dt):
        """Update the local player.

        This method computes player's game logic as a function of time and sends
        the appropriate event.

        :param dt: Time delta from last update.
        :type dt: float
        """
        super(Player, self).update(dt)

        x, y = self[Movable].position

        # update camera position
        context = Context.get_instance()
        context.camera.position = Vec(-x, -y)


@subscriber(PlayerJoin)
def add_player(evt):
    """Instantiate and add the local player into the game.

    :param evt: The event instance
    :type evt: :class:`game.events.PlayerJoin`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    resource = context.res_mgr.get('/characters/grunt')
    # Only instantiate the player if it does not exist
    if not context.resolve_entity(evt.srv_id):
        player = Player(resource, evt.name, context.scene.root)
        context.entities[player.e_id] = player
        context.server_entities_map[evt.srv_id] = player.e_id
        return player.e_id
