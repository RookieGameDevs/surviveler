from game import Entity
from game.components import Renderable
from matlib import Vec
from renderer import Rect
from renderer import Texture
from renderer import TextureParamFilter


WALKABLE = Vec(0, 1, 0)
NOT_WALKABLE = Vec(1, 0, 0)


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: The terrain resource
        :type resource: :class:`loaders.Resource`

        :param parent_node: Parent node to attach the terrain entity to.
        :type param_node: subclass of :class:`renderer.SceneNode`
        """
        matrix = resource.data['matrix']
        shader = resource['terrain_shader']

        w, h = len(matrix[0]), len(matrix)
        rect = Rect(w, h)

        texture = Texture.from_matrix(matrix)
        texture.set_param(TextureParamFilter(
            TextureParamFilter.Type.magnify,
            TextureParamFilter.Mode.nearest))

        renderable = Renderable(parent_node, rect, shader, textures=[texture])
        renderable.node.params['tex'] = texture

        super().__init__(renderable)

    def is_walkable(self, x, y):
        """Returns if the selected cell is walkable.

        :param x: The x in world coordinates
        :type x: int

        :param y: The y in world coordinates
        :type y: int

        :return: Wether the cell is walkable or not
        :rtype: bool
        """
        return bool(self.matrix[y][x])

    def update(self, dt):
        # NOTE: nothing to do here
        pass
