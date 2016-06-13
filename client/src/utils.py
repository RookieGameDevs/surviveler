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

    :return: number of milliseconds since epoch
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

    :return: the distance
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

    :return: the angle
    :rtype: float
    """
    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])


def to_scene(x, y):
    """Convert world coordinates to scene coordinates."""
    return Vec(x, 0, y)


def to_world(x, y, z):
    """Convert scene coordinates to world coordinates."""
    return Vec(x, z, 0)
