import math
import numpy as np


def vec3(x, y, z):
    """Shorthand function which creates a vector with 3 components.

    :param x: Value for X coordinate.
    :type x: float

    :param y: Value for Y coordinate.
    :type y: float

    :param z: Value for Z coordinate.
    :type z: float

    :returns: The resulting vector.
    :rtype: :class:`numpy.ndarray`
    """
    return np.array([x, y, z], np.float32)


#: Predefined vector for X axis
X_AXIS = vec3(1.0, 0.0, 0.0)
#: Predefined vector for Y axis
Y_AXIS = vec3(0.0, 1.0, 0.0)
#: Predefined vector for Z axis
Z_AXIS = vec3(0.0, 0.0, 1.0)

#: Predefined vector for up direction
UP = Y_AXIS
#: Predefined vector for forward direction
FORWARD = -Z_AXIS
#: Predefined vector for right direction
RIGHT = X_AXIS


def vec3_mag(v):
    """Returns the magnitude of a vector.

    :param v: Vector.
    :type v: :class:`numpy.ndarray`

    :returns: Vector's magnitude.
    :rtype: float
    """
    return np.sqrt(np.sum(i * i for i in v))


def vec3_unit(v):
    """Returns the normalized (unit) version of a vector.

    :param v: Original vector.
    :type v: :class:`numpy.ndarray`

    :returns: Normalized vector
    :rtype: :class:`numpy.ndarray`
    """
    mag = vec3_mag(v)
    if mag > 0:
        return v / mag
    return v


def mat4(t_mat=None, t_vec=None):
    """Creates a 4x4 homogeneous transformation matrix.

    :param t_mat: Transformation 3x3 matrix or None for identity.
    :type t_mat: instance of :class:`numpy.ndarray` or None

    :param t_vec: Translation vector or None for no translation.
    :type t_vec: :class:`numpy.ndarray` or None

    :returns: Resulting matrix.
    :rtype: :class:`numpy.matrix`
    """
    t_mat = t_mat if t_mat is not None else mat3()
    t_vec = t_vec if t_vec is not None else np.array([0.0, 0.0, 0.0], np.float32)
    mat = np.identity(4, np.float32)
    mat[0][:3] = t_mat[0]
    mat[1][:3] = t_mat[1]
    mat[2][:3] = t_mat[2]
    mat[:, 3][:3] = t_vec
    return np.matrix(mat)


def mat3():
    """Creates a 3x3 identity matrix.

    :returns: Resulting matrix.
    :rtype: :class:`numpy.matrix`
    """
    return np.matrix(np.identity(3, np.float32))


def mat3_rot(axis, theta):
    """Creates a 3x3 rotation matrix given an axis and angle.

    Returns the rotation matrix associated with counterclockwise rotation
    about the given axis by theta radians.

    :param axis: Three component vector which describes an axis.
    :type axis: :class:`numpy.ndarray`

    :param theta: Angle in radians.
    :type theta: float

    :returns: The resulting matrix.
    :rtype: :class:`numpy.matrix`
    """
    x = float(axis[0])
    y = float(axis[1])
    z = float(axis[2])
    sin_a = math.sin(theta)
    cos_a = math.cos(theta)
    k = 1 - math.cos(theta)

    mat = np.array([
        [cos_a + k * x * x, k * x * y - z * sin_a, k * x * z + y * sin_a],
        [k * x * y + z * sin_a, cos_a + k * y * y, k * y * z - x * sin_a],
        [k * x * z - y * sin_a, k * y * z + x * sin_a, cos_a + k * z * z],
    ], np.float32)
    return np.matrix(mat)
