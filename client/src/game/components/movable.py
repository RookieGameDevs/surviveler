from game.components import Component
from matlib import Vec
from utils import distance
import logging


LOG = logging.getLogger(__name__)


class Movable(Component):
    """Movable component.

    Given a destination and a target arrival timestamp, computes the position
    for each dt.
    """

    #: tolerance: if the current position is not different from the new "current
    # position" (the server one), we ignore the new one and continue with the
    # current interpolation.
    EPSILON = 0.1

    def __init__(self, position):
        """Constructor.

        :param position: The starting position of the movable.
        :type position: tuple
        """
        # Current position of the server
        self._position = position

        # Destination
        self._next_position = None

        # Path
        self._path = None

        # Speed
        self._speed = 0

        # Direction vector
        self._direction = None

    @property
    def position(self):
        """Current position getter.

        :return: The current position of the movable.
        :rtype: tuple
        """
        return self._position

    @position.setter
    def position(self, value):
        """Current position setter.

        :param value: The new position to be used as current.
        :type value: tuple
        """
        LOG.debug('Manually setting position {} -> {}'.format(
            self._position, value))
        self._next_position = None
        self._direction = None
        self._path = None
        self._speed = 0
        self._position = value

    @property
    def destination(self):
        """Destination getter.

        :return: The destination of the movable.
        :rtype: tuple or None
        """
        return self._next_position

    @destination.setter
    def destination(self, dest):
        """Destination setter."""
        self._next_position = dest

    @property
    def speed(self):
        """Speed getter.

        :return: The movable speed.
        :rtype: float
        """
        return self._speed

    def move(self, position, path, speed):
        """Initial setup of a movable.

        Sets the initial position, the movement path and the speed. And computes
        the direction vector.

        :param position: The starting position of the movable.
        :type position: :class:`tuple`

        :param path: The path to move by.
        :type path: list

        :param speed: The movement speed.
        :type target_tstamp: :class:`float`
        """
        # compute new direction
        self._speed = speed
        self._path = path
        self._position = position
        self.destination = path.pop(0)

    def update(self, dt):
        """Movable update function.

        Computes the amount of movement to be done in the given dt time. The
        movement is calculated using the speed and the direction of the
        movement.

        :param dt: The time spent since the last update call (in seconds).
        :type dt: float
        """
        if self._next_position:
            # We have both destination and speed, so we can calculate the amount
            # of movement in the given dt.
            self._direction = (
                Vec(self._next_position[0], self._next_position[1], 0.0) -
                Vec(self._position[0], self._position[1], 0.0))
            self._direction.norm()
            dv = self._direction * dt * self._speed
            self._position = self._position[0] + dv.x, self.position[1] + dv.y

            if distance(self._next_position, self._position) < self.EPSILON:
                self._position = self._next_position
                # Try to pick the next waypoint as new position
                try:
                    self.destination = self._path.pop(0)
                    LOG.debug('Switched destination to {}'.format(self.destination))
                except IndexError:
                    LOG.debug('Movable arrived at destination {}'.format(
                        self._position))
