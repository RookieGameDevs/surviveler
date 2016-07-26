from game.components import Renderable
from game.entities.entity import Entity
from matlib import Vec
from renderer.texture import Texture


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: The terrain resource
        :type resource: :class:`loaders.Resource`

        :param parent_node: Parent node to attach the terrain entity to.
        :type param_node: subclass of :class:`renderer.SceneNode`
        """
        shader = resource['shader']
        mesh = resource['floor_mesh']
        texture = Texture.from_image(resource['floor_texture'])
        # shader params
        params = {
            'tex': texture,
            'animate': 0,
        }
        renderable = Renderable(
            parent_node,
            mesh,
            shader,
            params,
            textures=[texture],
            enable_light=True)

        super().__init__(renderable)

        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        self[Renderable].transform.translate(Vec(0.0, 0.0, 1.0))

    def update(self, dt):
        # NOTE: nothing to do here
        pass
