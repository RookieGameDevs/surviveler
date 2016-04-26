import math
import numpy as np


def vec3(x, y, z):
    return np.array([x, y, z])


X_AXIS = vec3(1.0, 0.0, 0.0)
Y_AXIS = vec3(0.0, 1.0, 0.0)
Z_AXIS = vec3(0.0, 0.0, 1.0)


def mat4(t_mat=None, t_vec=None):
    t_mat = t_mat if t_mat is not None else mat3()
    t_vec = t_vec if t_vec is not None else np.array([0.0, 0.0, 0.0], np.float32)
    mat = np.identity(4, np.float32)
    mat[0][:3] = t_mat[0]
    mat[1][:3] = t_mat[1]
    mat[2][:3] = t_mat[2]
    mat[:, 3][:3] = t_vec
    return mat


def mat3():
    return np.identity(3, np.float32)


def mat3_rot(axis, theta):
    """Return the rotation matrix associated with counterclockwise rotation
    about the given axis by theta radians.
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
