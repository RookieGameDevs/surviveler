from abc import ABC
from abc import abstractproperty
from matlib import Mat
from matlib import Vec


class Camera(ABC):
    """Abstract Camera class.

    A camera abstracts model-view transformations on the scene in a intuitive
    way, that is, a point in the space (eye) looking at a given point (scene
    center).
    """

    def __init__(self):
        self.view_mat = Mat()
        self.position = Vec()

    def look_at(self, eye, center, up=None):
        """Sets up camera look transformation.

        :param eye: Eye (camera position) coordinates.
        :type eye: :class:`matlib.Vec`

        :param eye: Look at (scene center) coordinates.
        :type eye: :class:`matlib.Vec`

        :param up: Up vector.
        :type up: :class:`matlib.Vec`
        """
        up = up or Vec(0, 1, 0)

        # forward (Z axis)
        zaxis = center - eye
        dist = zaxis.mag()
        zaxis.norm()

        # right (X axis)
        xaxis = zaxis.cross(up)
        xaxis.norm()

        # up (Y axis)
        yaxis = xaxis.cross(zaxis)
        yaxis.norm()

        # orientation + translation matrix
        self.view_mat = Mat([
            Vec(xaxis.x, yaxis.x, -zaxis.x, 0),
            Vec(xaxis.y, yaxis.y, -zaxis.y, 0),
            Vec(xaxis.z, yaxis.z, -zaxis.z, dist),
            Vec(0,       0,       0,        1),
        ])

    @property
    def modelview(self):
        """Camera modelview 4x4 matrix."""
        t = Mat()
        t.translate(self.position)
        t *= self.view_mat
        return t

    @abstractproperty
    def projection(self):
        """Camera projection 4x4 matrix."""
        pass


class OrthoCamera(Camera):
    """Orthographic camera."""

    def __init__(self, left, right, top, bottom, distance):
        super(OrthoCamera, self).__init__()
        self.l = left
        self.r = right
        self.t = top
        self.b = bottom
        self.n = distance / 2
        self.f = self.n + distance

    @property
    def modelview(self):
        t = Mat()
        t.translate(Vec(0, 0, self.n))
        t *= super(OrthoCamera, self).modelview
        return t

    @property
    def projection(self):
        sx = 2.0 / (self.r - self.l)
        sy = 2.0 / (self.t - self.b)
        sz = 2.0 / (self.f - self.n)
        tx = -(self.r + self.l) / (self.r - self.l)
        ty = -(self.t + self.b) / (self.t - self.b)
        tz = -(self.f + self.n) / (self.f - self.n)
        proj_mat = Mat([
            Vec(sx, 0,  0,  tx),
            Vec(0,  sy, 0,  ty),
            Vec(0,  0,  sz, tz),
            Vec(0,  0,  0,  1),
        ])

        return proj_mat
