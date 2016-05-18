from game import Character
from game.components import Movable
from matlib import Vec3
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

        from client import Client
        client = Client.get_instance()
        client.camera.translate(-Vec3(x, y, 0))
