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


def mat4(t_mat=None, t_vec=None):
    """Creates a 4x4 homogeneous transformation matrix.

    :param t_mat: Transformation 3x3 matrix or None for identity.
    :type t_mat: instance of :class:`numpy.ndarray` or None

    :param t_vec: Translation vector or None for no translation.
    :type t_vec: :class:`numpy.ndarray` or None

    :returns: Resulting matrix.
    :rtype: :class:`numpy.ndarray`
    """
    t_mat = t_mat if t_mat is not None else mat3()
    t_vec = t_vec if t_vec is not None else np.array([0.0, 0.0, 0.0], np.float32)
    mat = np.identity(4, np.float32)
    mat[0][:3] = t_mat[0]
    mat[1][:3] = t_mat[1]
    mat[2][:3] = t_mat[2]
    mat[:, 3][:3] = t_vec
    return mat


def mat3():
    """Creates a 3x3 identity matrix.

    :returns: Resulting matrix.
    :rtype: :class:`numpy.ndarray`
    """
    return np.identity(3, np.float32)


def mat3_rot(axis, theta):
    """Creates a 3x3 rotation matrix given an axis and angle.

    Returns the rotation matrix associated with counterclockwise rotation
    about the given axis by theta radians.

    :param axis: Three component vector which describes an axis.
    :type axis: :class:`numpy.ndarray`

    :param theta: Angle in radians.
    :type theta: float

    :returns: The resulting matrix.
    :rtype: :class:`numpy.ndarray`
    """
    axis = np.asarray(axis)
    theta = np.asarray(theta)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])
