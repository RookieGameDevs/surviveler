from game.components import Component
from matlib.vec import Vec
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
        self.next_position = None

        # Path
        self.path = None

        # Speed
        self.speed = 0

        # Direction vector
        self._direction = None

    @property
    def position(self):
        """Current position getter.

        :returns: The current position of the movable.
        :rtype: tuple
        """
        return self._position

    @property
    def direction(self):
        return self._direction

    @position.setter
    def position(self, value):
        """Current position setter.

        :param value: The new position to be used as current.
        :type value: tuple
        """
        LOG.debug('Manually setting position {} -> {}'.format(
            self._position, value))
        self.next_position = None
        self._direction = None
        self.path = []
        self.speed = 0
        self._position = value

    @property
    def destination(self):
        return self.next_position

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
        self.speed = speed
        self.next_position = path[0]
        self.path = path[1:] if len(path) > 1 else []
        self._position = position

    def partial_movement(self, distance, position, next_position, path):
        """Recursive function to calculate parial movements (to consider cases
        in which during the given dt we are actually going over a the
        destination point.

        :param distance: The magnitude of the movement vector.
        :type distance: float

        :param position: The current position of the movable.
        :type position: tuple

        :param next_position: The next position in the path.
        :type next_position: tuple

        :param path: The other points of the path.
        :type path: list
        """
        # Actual distance from destination
        np = Vec(next_position[0], next_position[1], 0.0)
        p = Vec(position[0], position[1], 0.0)
        dst = (np - p).mag()

        # We did not reach the next_position yet.
        if distance < dst:
            self._direction = np - p
            self._direction.norm()
            cur = p + self._direction * distance
            self._position = cur.x, cur.y

        # We arrived in next_position, continue toward the next waypoint of the
        # path recursively calling partial_movement.
        elif path:
            position, next_position, path = next_position, path[0], path[1:]
            LOG.debug('Switched destination to {}'.format(next_position))
            self.partial_movement(
                distance - dst, position, next_position, path)

        # We reached or surpassed next_position and there are no more path
        # steps: we arrived!
        else:
            LOG.debug('Movable arrived at destination {}'.format(self._position))
            self.next_position = None
            self._direction = None
            self.path = []
            self.speed = 0
            self._position = next_position

    def update(self, dt):
        """Movable update function.

        Computes the amount of movement to be done in the given dt time. The
        movement is calculated using the speed and the direction of the
        movement.

        :param dt: The time spent since the last update call (in seconds).
        :type dt: float
        """
        if self.next_position and self.speed:
            distance = self.speed * dt
            self.partial_movement(
                distance, self._position, self.next_position, self.path)
