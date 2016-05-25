from game import Entity
from game.components import Renderable
from matlib import Vec
from renderer import Rect
from renderer import Texture
from renderer import TextureParamWrap


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, resource, parent_node, width, height):
        """Constructor.

        :param resource: The terrain resource
        :type resource: :class:`loaders.Resource`

        :param parent_node: Parent node to attach the terrain entity to.
        :type param_node: subclass of :class:`renderer.SceneNode`

        :param width: Width of the terrain in game units.
        :type width: float

        :param height: Height of the terrain in game units.
        :type height: float
        """
        mesh = Rect(1, 1)

        shader = resource['shader']
        tiles = resource['tiles']

        texture = Texture.from_image(tiles)
        texture.set_param(TextureParamWrap(
            TextureParamWrap.Coord.s, TextureParamWrap.WrapType.repeat))
        texture.set_param(TextureParamWrap(
            TextureParamWrap.Coord.t, TextureParamWrap.WrapType.repeat))

        renderable = Renderable(parent_node, mesh, shader, textures=[texture])
        renderable.node.params['tex'] = texture

        t = renderable.transform
        t.translate(Vec(-50, -50, 0.5))
        t.scale(Vec(100, 100, 1))

        super(Terrain, self).__init__(renderable)

    def update(self, dt):
        # NOTE: nothing to do
        pass
