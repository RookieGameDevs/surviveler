from abc import ABC
from matlib.mat import Mat
from matlib.vec import Vec


class Camera(ABC):
    """Abstract Camera class.

    A camera abstracts model-view transformations on the scene in a intuitive
    way, that is, a point in the space (eye) looking at a given point (scene
    center).
    """

    def __init__(self):
        self.position = Vec()
        self.translate_mat = Mat()
        self.modelview_mat = Mat()
        self.projection_mat = Mat()

    def set_position(self, center):
        """Sets the position of the center of the scene.

        :param center: The new center of the scene
        :type center: :class:`matlib.Vec`
        """
        self.position = center
        self.translate_mat.ident()
        self.translate_mat.translatev(-center)

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
        self.modelview_mat.ident()
        self.modelview_mat.lookatv(eye, center, up)

    def unproject(self, vx, vy, vz, vw, vh):
        """Unprojects a point in viewport coordinates into world coordinates.

        :param vx: Viewport X coordinate.
        :type vx: float

        :param vy: Viewport Y coordinate.
        :type vy: float

        :param vz: Viewport Z coordinate in range [0, 1].
        :type vz: float

        :param vw: Viewport width.
        :type vw: float

        :param vh: Viewport height.
        :type vh: float

        :returns: Unprojected point in world coordinates.
        :rtype: :class:`matlib.Vec`
        """
        x_ndc = 2.0 * vx / vw - 1.0
        y_ndc = 1.0 - (2.0 * vy) / vh
        z_ndc = 2 * vz - 1
        w_ndc = 1.0
        v_clip = Vec(x_ndc, y_ndc, z_ndc, w_ndc)

        m = self.projection * self.modelview
        m.inverse()

        out = m * v_clip
        out.w = 1.0 / out.w
        out.x *= out.w
        out.y *= out.w
        out.z *= out.w
        return out

    def trace_ray(self, vx, vy, vw, vh):
        """Traces a ray from viewport point "into the screen" and returns the
        ray origin and direction vector.

        :param vx: Viewport X coordinate.
        :type vx: float

        :param vy: Viewport Y coordinate.
        :type vy: float

        :param vw: Viewport width.
        :type vw: float

        :param vh: Viewport height.
        :type vh: float

        :returns: A tuple with the origin being first element and normalized
            direction vector the second.
        :rtype: (:class:`matlib.Vec`, :class:`matlib.Vec`)
        """
        p1 = self.unproject(vx, vy, 0, vw, vh)
        p2 = self.unproject(vx, vy, 1, vw, vh)
        ray = p2 - p1
        ray.norm()
        return p1, ray

    @property
    def modelview(self):
        """Camera modelview 4x4 matrix."""
        return self.modelview_mat * self.translate_mat

    @property
    def projection(self):
        """Camera projection 4x4 matrix."""
        return self.projection_mat


class OrthoCamera(Camera):
    """Orthographic camera."""

    def __init__(self, left, right, top, bottom, near, far):
        """Constructor. Initializes an orthographic projection camera.

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
        self.projection_mat.ortho(left, right, top, bottom, near, far)


class PerspCamera(Camera):
    """Orthographic camera."""

    def __init__(self, fovy, aspect, near, far):
        """Constructor. Initializes a perspective projection camera.

        :param fovy: Vertical FOV.
        :type fovy: float

        :param aspect: Aspect ratio (w / h)
        :type aspect: float

        :param near: The near clipping plane
        :type near: float

        :param far: The far clipping plane
        :type far: float
        """
        super(PerspCamera, self).__init__()
        self.projection_mat.persp(fovy, aspect, near, far)
