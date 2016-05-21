from game import Entity
from game.components import Renderable
from matlib import Mat4
from matlib import Vec3
from renderer import Rect
from renderer import Shader
from renderer import Texture
from renderer import TextureParamWrap


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, parent_node, width, height):
        """Constructor.

        :param parent_node: Parent node to attach the terrain entity to.
        :type param_node: subclass of :class:`renderer.SceneNode`

        :param width: Width of the terrain in game units.
        :type width: float

        :param height: Height of the terrain in game units.
        :type height: float
        """
        mesh = Rect(1, 1)

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
            Mat4.trans(Vec3(-50, -50, 0.5)) *
            Mat4.scale(Vec3(100, 100, 1)))

        super(Terrain, self).__init__(renderable)

    def update(self, dt):
        # NOTE: nothing to do
        pass
