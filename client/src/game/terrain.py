from game import Entity
from game.components import Renderable
from matlib import Mat4
from matlib import Vec3
from renderer import Mesh
from renderer import Shader
from renderer import Texture
from renderer import TextureParamWrap


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
        uvs = [
            0, 0,
            0, 1,
            1, 1,
            1, 0,
        ]
        mesh = Mesh(vertices, indices, uvs)

        shader = Shader.from_glsl(
            'data/shaders/terrain.vert',
            'data/shaders/terrain.frag')

        texture = Texture.from_file('data/textures/tiles.jpg')
        texture.set_param(TextureParamWrap(
            TextureParamWrap.Coord.s, TextureParamWrap.WrapType.repeat))
        texture.set_param(TextureParamWrap(
            TextureParamWrap.Coord.t, TextureParamWrap.WrapType.repeat))

        renderable = Renderable(parent_node, mesh, shader, textures=[texture])
        renderable.node.params['tex'] = texture
        renderable.transform = (
            Mat4.trans(Vec3(0, 0, 0.5)) *
            Mat4.scale(Vec3(100, 100, 1)))
        super(Terrain, self).__init__(renderable)

    def update(self, dt):
        pass
