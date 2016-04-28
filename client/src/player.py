from math import pi
from matlib import Y_AXIS
from matlib import mat3_rot
from matlib import mat4
from renderer import GeometryNode
from renderer import Mesh
from renderer import Shader


WHOLE_ANGLE = 2.0 * pi

MESH_VERTICES = [
    +0.0, +0.3, 0.0,
    -0.3, -0.3, 0.0,
    +0.3, -0.3, 0.0,
]

MESH_INDICES = [
    0, 1, 2,
]


class Player:
    """Game entity which represents a player."""

    def __init__(self):
        mesh = Mesh(MESH_VERTICES, MESH_INDICES)
        shader = Shader.from_glsl(
            'data/shaders/simple.vert',
            'data/shaders/simple.frag')

        self._node = GeometryNode(mesh, shader)

        self.rot_angle = 0.0

    @property
    def node(self):
        """Scene node associated with player's entity."""
        return self._node

    def update(self, dt):
        """Update the player.

        This method computes player's game logic as a function of time.

        :param dt: Time delta from last update.
        :type dt: float
        """
        self.rot_angle += dt * pi
        if self.rot_angle >= WHOLE_ANGLE:
            self.rot_angle -= WHOLE_ANGLE

        self._node.transform = mat4(mat3_rot(Y_AXIS, self.rot_angle))
