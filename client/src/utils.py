from datetime import datetime
from matlib import Vec
import math


def as_ascii(b):
    """Transform a byte array into an ASCII string.

    :param b: byte sequence to convert to string
    :type b: bytes or bytearray
    """
    return b.decode('ascii')


def as_utf8(b):
    """Transform a byte array into an UTF-8 string.

    :param b: byte sequence to convert to string
    :type b: bytes or bytearray
    """
    return b.decode('utf8')


def tstamp(dt=None):
    """Returns the number of milliseconds since epoch.

    :param dt: the compared datetime object
    :type dt: :class:`datetime.datetime` or None

    :returns: number of milliseconds since epoch
    :rtype: int
    """
    dt = dt or datetime.utcnow()
    return int((dt - datetime(1970, 1, 1)).total_seconds() * 1000)


def distance(p1, p2):
    """Returns the distance between the two points.

    :param p1: the first point
    :type p1: tuple

    :param p2: the second point
    :type p2: tuple

    :returns: the distance
    :rtype: float
    """
    return math.sqrt(
        math.pow(p2[0] - p1[0], 2) +
        math.pow(p2[1] - p1[1], 2))


def angle(p1, p2):
    """Returns the angle of the vector that goes from p1 to p2.

    :param p1: the first point
    :type p1: tuple

    :param p2: the second point
    :type p2: tuple

    :returns: the angle
    :rtype: float
    """
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])


def to_scene(x, y):
    """Convert world coordinates to scene coordinates."""
    return Vec(x, 0, y)


def to_world(x, y, z):
    """Convert scene coordinates to world coordinates."""
    return Vec(x, z, 0)


def clamp_to_grid(x, y, scale_factor):
    """Clamp x and y to the grid with scale factor scale_factor.

    :param x: The x coordinate in world coordinates.
    :type x: float

    :param y: The y coordinate in world coordinates.
    :type y: float

    :param scale_factor: The scale factor of the grid.
    :type scale_factor: int

    :return: The clamped coordinates.
    :rtype: tuple
    """
    c_x = math.copysign(
        math.floor(x * scale_factor) / scale_factor + 1 / (scale_factor * 2), x)

    c_y = math.copysign(
        math.floor(y * scale_factor) / scale_factor + 1 / (scale_factor * 2), y)

    return c_x, c_y


def to_matrix(g_x, g_y, scale_factor):
    """Convert the grid x and y to matrix indices using the matrix scale factor.

    :param g_x: The x coordinate in world coordinates.
    :type g_x: float

    :param g_y: The y coordinate in world coordinates.
    :type g_y: float

    :param scale_factor: The scale factor of the grid.
    :type scale_factor: int

    :return: The clamped coordinates.
    :rtype: tuple
    """
    x = (g_x - 1 / (scale_factor * 2)) * scale_factor
    y = (g_y - 1 / (scale_factor * 2)) * scale_factor

    return int(x), int(y)
