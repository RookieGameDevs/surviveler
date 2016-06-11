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
        self.translate_mat = Mat()
        self.modelview_mat = Mat()

    def set_position(self, center):
        """Sets the position of the center of the scene.

        :param center: The new center of the scene
        :type center: :class:`matlib.Vec`
        """
        self.translate_mat.identity()
        self.translate_mat.translate(-center)

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

        z = eye - center
        z.norm()

        x = up.cross(z)
        x.norm()

        y = z.cross(x)
        y.norm()

        self.view_mat = Mat([
            Vec(x.x, y.x, z.x, 0),
            Vec(x.y, y.y, z.y, 0),
            Vec(x.z, y.z, z.z, 0),
            Vec(0, 0, 0, 1),
        ])

    def unproject(self, vx, vy, vw, vh):
        """Computes the unprojected point from viewport coordinates.

        :param vx: Viewport X coordinate.
        :type vx: int

        :param vy: Viewport Y coordinate.
        :type vy: int

        :param vw: Viewport width.
        :type vw: int

        :param vh: Viewport height.
        :type vh: int

        :returns: The point on the viewport in world coordinates.
        :rtype: :class:`matlib.Vec`
        """
        # transform viewport coordinates to NDC space
        x_ndc = 2.0 * vx / vw - 1.0
        y_ndc = 1.0 - 2 * vy / vh

        # transform NDC coordinates to homogeneous clip coordinates by making a
        # 4D vector pointing to negative Z and having W set to 1.0
        v_clip = Vec(x_ndc, y_ndc, -1, 1.0)

        # transform clip coordinates to eye space by unprojecting them using
        # camera's projection matrix's inverse
        m_projection = Mat(self.projection)
        m_projection.invert()
        v_eye = m_projection * v_clip

        # change the vector so that only X and Y components are used, Z and W is
        # of no use
        v_eye.z = 0.0
        v_eye.w = 0.0

        v_world = self.view_mat * v_eye
        v_world -= Vec(
            self.translate_mat[0, 3],
            self.translate_mat[1, 3],
            self.translate_mat[2, 3],
        )

        return v_world

    @property
    def modelview(self):
        """Camera modelview 4x4 matrix."""
        return self.view_mat * self.translate_mat

    @abstractproperty
    def projection(self):
        """Camera projection 4x4 matrix."""
        pass


class OrthoCamera(Camera):
    """Orthographic camera."""

    def __init__(self, left, right, top, bottom, near, far):
        """Creates the orthocamera with the various parameters needed.

        :param left: The left boundary
        :type left: float

        :param right: The right boundary
        :type right: float

        :param top: The top boundary
        :type top: float

        :param bottom: The bottom boundary
        :type bottom: float

        :param near: The near clipping plane
        :type near: float

        :param far: The far clipping plane
        :type far: float
        """
        super(OrthoCamera, self).__init__()
        self.l = left
        self.r = right
        self.t = top
        self.b = bottom
        self.n = near
        self.f = far

    @property
    def modelview(self):
        """Camera modelview 4x4 matrix."""
        t = super().modelview
        m = Mat(self.view_mat)
        m.invert()
        t.translate(m * Vec(0, 0, -(self.n + self.f) / 2))
        return t

    @property
    def projection(self):
        """Camera projection 4x4 matrix."""
        sx = 2.0 / (self.r - self.l)
        sy = 2.0 / (self.t - self.b)
        sz = -2.0 / (self.f - self.n)
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
