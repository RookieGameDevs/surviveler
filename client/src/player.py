from math import pi
from matlib import Y_AXIS
from matlib import mat3_rot
from matlib import mat4
from renderer import GeometryNode
from renderer import Mesh
from renderer import Shader


MESH_VERTICES = [
    +0.0, +0.3, 0.0,
    -0.3, -0.3, 0.0,
    +0.3, -0.3, 0.0,
]

MESH_INDICES = [
    0, 1, 2,
]


class Player:

    def __init__(self):
        mesh = Mesh(MESH_VERTICES, MESH_INDICES)
        shader = Shader.from_glsl(
            'data/shaders/simple.vert',
            'data/shaders/simple.frag')

        self.scene_node = GeometryNode(mesh, shader)

        self.rot_angle = 0.0

    def get_node(self):
        return self.scene_node

    def update(self, dt):
        self.rot_angle = dt * 2 * pi / 10.0
        self.scene_node.transform = mat4(mat3_rot(Y_AXIS, self.rot_angle))
