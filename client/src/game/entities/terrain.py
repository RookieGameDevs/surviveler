from game.components import Renderable
from game.entities.entity import Entity
from renderer import Rect
from renderer import Texture
from renderer import TextureParamFilter


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: The terrain resource
        :type resource: :class:`loaders.Resource`

        :param parent_node: Parent node to attach the terrain entity to.
        :type param_node: subclass of :class:`renderer.SceneNode`
        """
        scale_factor = resource.data['scale_factor']
        matrix = resource['matrix']
        shader = resource['terrain_shader']

        w, h = len(matrix[0]), len(matrix)
        rect = Rect(w / scale_factor, h / scale_factor)

        texture = self.prepare_walkable_matrix(matrix)

        renderable = Renderable(parent_node, rect, shader, textures=[texture])
        renderable.node.params['tex'] = texture

        super().__init__(renderable)

    def update(self, dt):
        # NOTE: nothing to do here
        pass

    def set_walkable_state(self, matrix):
        """Set the current matrix as terrain.

        :param matrix: The matrix to be used
        :type matrix: :class:`list`
        """
        texture = self.prepare_walkable_matrix(matrix)
        node = self[Renderable].node
        node.params['tex'] = texture
        node.textures = [texture]

    def prepare_walkable_matrix(self, matrix):
        """Prepare the debug terrain texture using the source matrix.

        :param matrix: The source matrix of walkable areas
        :type matrix: :class:`list`

        :returns: The walkable debug terrain
        :rtype: :class:`renderer.Texture`
        """
        texture = Texture.from_matrix(matrix)
        texture.set_param(TextureParamFilter(
            TextureParamFilter.Type.magnify,
            TextureParamFilter.Mode.nearest))

        return texture
