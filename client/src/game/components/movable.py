from game.components import Component
from matlib import Vec3
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
        self._destination = None

        # Speed
        self._speed = 0

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
        self._position = value

    @property
    def destination(self):
        """Destination getter.

        :return: The destination of the movable.
        :rtype: tuple or None
        """
        return self._destination

    @property
    def speed(self):
        """Speed getter.

        :return: The movable speed.
        :rtype: float
        """
        return self._speed

    def move(self, position, destination, speed):
        """Initial setup of a movable.

        Set the initial position, the destination and the speed. And compute the
        direction vector.

        :param position: The starting position of the movable.
        :type position: :class:`tuple`

        :param destination: The target destination of the movable.
        :type destination: :class:`tuple`

        :param speed: The movement speed.
        :type target_tstamp: :class:`float`
        """
        LOG.debug('Moving movable from {} to {} at speed {}'.format(
            position, destination, speed))
        self.direction = (
            Vec3(destination[0], destination[1], 0.0) -
            Vec3(position[0], position[1], 0.0)).unit()
        self._position = position
        self._destination = destination
        self._speed = speed

    def update(self, dt):
        """Movable update function.

        Computes the amount of movement to be done in the given dt time. The
        movement is calculated using the speed and the direction of the
        movement.

        :param dt: The time spent since the last update call (in seconds).
        :type dt: float
        """
        if self._destination:
            # We have both destination and target timestamp, we can calculate
            # the amount of movement in the given dt.
            dv = self.direction * dt * self._speed
            self._position = self._position[0] + dv.x, self.position[1] + dv.y

            if distance(self._destination, self._position) < self.EPSILON:
                # Reset the movable internal data because we arrived at the
                # destination (distance < EPSILON). Force the destination as
                # current position and reset the internal data.
                self._position = self._destination
                self._destination, self.direction = None, None
                LOG.debug('Movable arrived at destination {}'.format(
                    self._position))
