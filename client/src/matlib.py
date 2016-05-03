import math
import numpy as np


class Vec3(np.ndarray):
    """Vector with X,Y,Z components."""

    def __new__(cls, x=0, y=0, z=0):
        """Constructor.

        :param x: X component value.
        :type x: float

        :param y: Y component value.
        :type y: float

        :param z: Z component value.
        :type z: float

        NOTE: due to the mechanics of subclassing `numpy.ndarray`, the
        `__new__()` method is overriden instead of `__init__()`.
        """
        vec = np.ndarray.__new__(cls, shape=(3,), dtype=np.float32)
        vec[0] = x
        vec[1] = y
        vec[2] = z
        return vec

    def cross(self, other):
        """Returns cross product vector.

        :param other: The vector to perform cross product by.
        :type other: :class:`matlib.Vec3`

        :returns: Normalized vector.
        :rtype: :class:`matlib.Vec3`
        """
        x, y, z = np.cross(self, other)
        return Vec3(x, y, z)

    def dot(self, other):
        """Returns dot product with another vector.

        :param other: The vector to perform dot product by.
        :type other: :class:`matlib.Vec3`

        :returns: Dot product.
        :rtype: float
        """
        x, y, z = np.dot(self, other)
        return Vec3(x, y, z)

    def mag(self):
        """Returns the magnitude of a vector.

        :returns: Vector's magnitude.
        :rtype: float
        """
        return np.sqrt(np.sum(i * i for i in self))

    def unit(self):
        """Returns the normalized (unit) version of the vector.

        :returns: Normalized vector.
        :rtype: :class:`matlib.Vec3`
        """
        return self / self.mag()


class Mat4(np.matrix):
    """Matrix 4x4."""

    def __new__(cls, rows=None):
        return np.matrix.__new__(cls, rows or np.eye(4), np.float32)

    @classmethod
    def rot(cls, axis, theta):
        """Creates a rotation matrix given an axis and angle.

        Returns the rotation matrix associated with counterclockwise rotation
        about the given axis by theta radians.

        :param axis: Three component vector which describes an axis.
        :type axis: :class:`matlib.Vec3`

        :param theta: Angle in radians.
        :type theta: float

        :returns: The resulting matrix.
        :rtype: :class:`matlib.Mat4`
        """
        x = float(axis[0])
        y = float(axis[1])
        z = float(axis[2])
        sin_a = math.sin(theta)
        cos_a = math.cos(theta)
        k = 1 - math.cos(theta)

        return Mat4([
            [cos_a + k * x * x, k * x * y - z * sin_a, k * x * z + y * sin_a, 0],
            [k * x * y + z * sin_a, cos_a + k * y * y, k * y * z - x * sin_a, 0],
            [k * x * z - y * sin_a, k * y * z + x * sin_a, cos_a + k * z * z, 0],
            [0, 0, 0, 1],
        ])

    @classmethod
    def trans(cls, v):
        """Creates a translation matrix given the translation vector.

        :param v: Translation vector.
        :type v: :class:`matlib.Vec3`

        :returns: The resulting matrix.
        :rtype: :class:`matlib.Mat4`
        """
        mat = Mat4()
        mat.A[:, 3][:3] = v
        return mat

    @classmethod
    def scale(cls, v):
        """Creates a scale matrix given scale factors.

        :param v: Scale vector.
        :type v: :class:`matlib.Vec3`

        :returns: The resulting matrix.
        :rtype: :class:`matlib.Mat4`
        """
        return Mat4([
            [v[0], 0,    0,    0],
            [0,    v[1], 0,    0],
            [0,    0,    v[2], 0],
            [0,    0,    0,    1],
        ])


#: Predefined vector for X axis
X = Vec3(1.0, 0.0, 0.0)

#: Predefined vector for Y axis
Y = Vec3(0.0, 1.0, 0.0)

#: Predefined vector for Z axis
Z = Vec3(0.0, 0.0, 1.0)

#: Predefined vector for up direction
UP = Y

#: Predefined vector for forward direction
FORWARD = -Z

#: Predefined vector for right direction
RIGHT = X
