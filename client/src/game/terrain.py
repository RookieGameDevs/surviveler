from game import Entity
from game.components import Renderable
from matlib import Mat4
from matlib import Vec3
from renderer import Mesh
from renderer import Shader


class Terrain(Entity):

    def __init__(self, parent_node, width, height):
        vertices = [
            -0.5, +0.5, +0.0,  # top left
            -0.5, -0.5, +0.0,  # bottom left
            +0.5, -0.5, +0.0,  # bottom right
            +0.5, +0.5, +0.0,  # top right
        ]
        indices = [
            2, 1, 0,
            3, 2, 0,
        ]
        mesh = Mesh(vertices, indices)
        shader = Shader.from_glsl(
            'data/shaders/simple.vert',
            'data/shaders/simple.frag')
        renderable = Renderable(parent_node, mesh, shader)
        renderable.node.params['color'] = Vec3(0, 1, 0)
        renderable.transform = (
            Mat4.trans(Vec3(0, 0, 0.5)) *
            Mat4.scale(Vec3(100, 100, 1)))
        super(Terrain, self).__init__(renderable)

    def update(self, dt):
        pass
