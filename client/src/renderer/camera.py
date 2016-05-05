from abc import ABC
from abc import abstractproperty
from matlib import UP
from matlib import Mat4
from matlib import Vec3


class Camera(ABC):
    """Abstract Camera class.

    A camera abstracts model-view transformations on the scene in a intuitive
    way, that is, a point in the space (eye) looking at a given point (scene
    center).
    """

    def __init__(self):
        self.view_mat = Mat4()
        self.scale_vec = Vec3(1.0, 1.0, 1.0)

    def zoom(self, factor):
        self.scale_vec = Vec3(factor, factor, factor)

    def look_at(self, eye, center, up=UP):
        """Sets up camera look transformation.

        :param eye: Eye (camera position) coordinates.
        :type eye: :class:`matlib.Vec3`

        :param eye: Look at (scene center) coordinates.
        :type eye: :class:`matlib.Vec3`

        :param up: Up vector.
        :type up: :class:`matlib.Vec3`
        """
        d = eye - center
        z = d.unit()
        x = up.cross(z).unit()
        if x.mag() == 0:
            raise ValueError(
                'Look direction vector must be different from up vector')

        y = z.cross(x)
        self.view_mat = (
            Mat4([
                [x[0],  x[1],  x[2],  0],
                [y[0],  y[1],  y[2],  0],
                [z[0],  z[1],  z[2],  0],
                [0,     0,     0,     1]
            ]) *
            Mat4.trans(d))

    @property
    def modelview(self):
        """Camera modelview 4x4 matrix."""
        return Mat4.scale(self.scale_vec) * self.view_mat

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
        return (
            Mat4.trans(Vec3(0, 0, self.n)) *
            super(OrthoCamera, self).modelview)

    @property
    def projection(self):
        sx = 2.0 / (self.r - self.l)
        sy = 2.0 / (self.t - self.b)
        sz = 2.0 / (self.f - self.n)
        tx = -(self.r + self.l) / (self.r - self.l)
        ty = -(self.t + self.b) / (self.t - self.b)
        tz = -(self.f + self.n) / (self.f - self.n)
        proj_mat = Mat4([
            [sx, 0,  0,  tx],
            [0,  sy, 0,  ty],
            [0,  0,  sz, tz],
            [0,  0,  0,  1],
        ])

        return proj_mat
