from game.components import Component
from utils import angle
from utils import distance
from utils import tstamp
import logging
import math


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

        # Current timestamp (for movement interpolation)
        self._current_tstamp = 0
        # Current destination (for movement interpolation)
        self._destination = None
        # Target timestamp (for movement interpolation)
        self._target_tstamp = None

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
        if distance(value, self._position) > self.EPSILON:
            self._position = value
        else:
            LOG.debug('Ignoring position changes: {} {}'.format(
                self._position, value))

    @property
    def destination(self):
        """Destination getter.

        :return: The destination of the movable.
        :rtype: tuple or None
        """
        return self._destination

    @property
    def target_tstamp(self):
        """Target timestamp getter.

        :return: The timestamp (local time) in which the movable is expected to
            be in the destination point.
        :rtype: int or None
        """
        return self._target_tstamp

    def move(self, position, start_tstamp, destination, target_tstamp):
        """Initial setup of a movable.

        Computes the initial position, based on the starting position and the dt
        from the the tstamp when the starting position was calculated on the
        server.

        :param position: The starting position of the movable.
        :type position: :class:`tuple`

        :param start_tstamp: The timestamp in which the starting position was
            calculated
        :type start_tstamp: :class:`int`

        :param destination: The target destination of the movable.
        :type destination: :class:`tuple`

        :param target_tstamp: The timestamp in which the movable is expected to
            be at destination
        :type target_tstamp: :class:`int`
        """
        dst = distance(destination, position)
        theta = angle(self._position, self._destination)
        now = tstamp()
        dst = (
            tstamp() - start_tstamp *
            distance(destination, position) /
            (target_tstamp - start_tstamp))

        # Use the EPSILON tolerance calculation as usual to decide if we really
        # need to move the movable.
        self.position = (
            position[0] + dst * math.cos(theta),
            position[1] + dst * math.sin(theta))

        self._current_tstamp = now
        self._destination = destination
        self._target_tstamp = target_tstamp

    def update(self, dt):
        """Movable update function.

        Computes the amount of movement to be done in the given dt time. The
        movement is calculated using the target tstamp and the distance between
        the current position and the destination.

        NOTE: inside this method we are talking about milliseconds: the dt
        parameter is converted in milliseconds and all the timing logics are in
        milliseconds.

        :param dt: The time spent since the last update call (in seconds).
        :type dt: float
        """
        if self._destination and self._target_tstamp:
            # We have both destination and target timestamp, we can calculate
            # the amount of movement in the given dt.
            ms_dt = dt * 1000
            theta = angle(self._position, self._destination)
            dst = (
                ms_dt *
                distance(self._position, self._destination) /
                (self._target_tstamp - self._current_tstamp))
            self._position = (
                self._position[0] + dst * math.cos(theta),
                self._position[1] + dst * math.sin(theta))

            self._current_tstamp += ms_dt

            finished = (
                distance(self._destination, self._position) < self.EPSILON or
                self._target_tstamp - self._current_tstamp == 0)
            if finished:
                # Reset the movable internal data because:
                #  1. We arrived at the destination (distance < EPSILON)
                #  2. We are in the target timestamp instant
                # Force the destination as current position and reset the
                # internal data.
                self._position = self._destination
                self._destination, self._target_tstamp = None, None
                self._current_tstamp = 0
