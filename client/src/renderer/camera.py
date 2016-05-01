from abc import ABC
from abc import abstractproperty
from matlib import UP
from matlib import Mat4


class Camera(ABC):
    """Abstract Camera class.

    A camera abstracts model-view transformations on the scene in a intuitive
    way, that is, a point in the space (eye) looking at a given point (scene
    center).
    """

    def __init__(self):
        self.look_t = Mat4()

    def look_at(self, eye, center, up=UP):
        """Sets up camera look transformation.

        :param eye: Eye (camera position) coordinates.
        :type eye: :class:`matlib.Vec3`

        :param eye: Look at (scene center) coordinates.
        :type eye: :class:`matlib.Vec3`

        :param up: Up vector.
        :type up: :class:`matlib.Vec3`
        """
        t = center - eye
        z = t.mag()
        f = t.unit()
        s = f.cross(up)
        if s.mag() == 0:
            raise ValueError(
                'Look direction vector must be different from up vector')

        u = s.unit().cross(f)
        self.look_t = Mat4([
            [s[0],  s[1],  s[2],  0],
            [u[0],  u[1],  u[2],  0],
            [-f[0], -f[1], -f[2], z],
            [0,     0,     0,     1]
        ])

    @abstractproperty
    def transform(self):
        """Camera transformation 4x4 matrix."""
        pass


class OrthoCamera(Camera):
    """Orthographic camera."""

    def __init__(self, left, right, top, bottom, distance):
        super(OrthoCamera, self).__init__()
        self.l = left
        self.r = right
        self.t = top
        self.b = bottom
        self.n = 0
        self.f = distance

    @property
    def transform(self):
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

        return proj_mat * self.look_t
