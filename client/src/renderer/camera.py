from abc import ABC
from matlib import Mat
from matlib import Vec


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
        self.modelview_mat.identity()
        self.modelview_mat.lookat(eye, center, up)

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

        v_world = self.modelview_mat * v_eye
        v_world -= Vec(
            self.translate_mat[0, 3],
            self.translate_mat[1, 3],
            self.translate_mat[2, 3],
        )

        return v_world

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
