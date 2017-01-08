from datetime import datetime
from matlib.vec import Vec
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


def intersection(pos, ray, norm, d):
    """Find the intersection between the ray and the playe defined by norm and
    offset d from origin.

    :param pos: The origin of the ray
    :type pos: :class:`matlib.Vec`

    :param ray: The ray
    :type ray: :class:`matlib.Vec`

    :param norm: The plane normal
    :type norm: :class:`matlib.Vec`

    :param d: The distance from origin
    :type d: :class:`matlib.Vec`
    """
    t = -(pos.dot(norm) + d) / ray.dot(norm)
    return pos + (ray * t)


def intersect(pos, ray, bb):
    """Check if the ray starting from position pos intersects the bounding box.

    :param pos: The origin of the ray
    :type pos: :class:`matlib.Vec`

    :param ray: The ray
    :type ray: :class:`matlib.Vec`

    :param bb: The entity bounding box
    :type bb: :class:`tuple`
    """
    # FIXME: please generalize me
    l, m = bb
    # front plane
    p = intersection(pos, ray, Vec(0, 0, -1), m.z)
    if l.x <= p.x <= m.x and l.y <= p.y <= m.y:
        return True
    # left plane
    p = intersection(pos, ray, Vec(1, 0, 0), l.x)
    if l.y <= p.y <= m.y and l.z <= p.z <= m.z:
        return True
    # right plane
    p = intersection(pos, ray, Vec(-1, 0, 0), m.x)
    if l.y <= p.y <= m.y and l.z <= p.z <= m.z:
        return True
    # top plane
    p = intersection(pos, ray, Vec(0, -1, 0), m.y)
    if l.x <= p.x <= m.x and l.z <= p.z <= m.z:
        return True
    # back plane
    p = intersection(pos, ray, Vec(1, 0, 0), l.z)
    if l.x <= p.x <= m.x and l.y <= p.y <= m.y:
        return True

    return False


def clamp_to_grid(x, y, scale_factor):
    """Clamp x and y to the grid with scale factor scale_factor.

    :param x: The x coordinate in world coordinates.
    :type x: float

    :param y: The y coordinate in world coordinates.
    :type y: float

    :param scale_factor: The scale factor of the grid.
    :type scale_factor: int

    :returns: The clamped coordinates.
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

    :returns: The clamped coordinates.
    :rtype: tuple
    """
    x = (g_x - 1 / (scale_factor * 2)) * scale_factor
    y = (g_y - 1 / (scale_factor * 2)) * scale_factor

    return int(x), int(y)


def in_matrix(matrix, x, y):
    """Check if the specified coordinates are inside the matrix.

    :param matrix: The matrix.
    :type matrix: list

    :param x: The x coordinate.
    :type x: int

    :param y: The y coordinate.
    :type y: int

    :returns: True if the point is inside the matrix, otherwise False
    :rtype: bool
    """
    return len(matrix) > y and len(matrix[y]) > x
