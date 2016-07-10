from game.components import Renderable
from game.entities.entity import Entity
from matlib import Vec


class Map(Entity):
    """Map entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: Resource containing map data.
        :type resource: :class:`resource_manager.Resource`

        :param parent_node: Node to attach the map to.
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        mesh = resource['mesh']
        shader = resource['walls_shader']

        params = {
            'color_ambient': Vec(0.4, 0.4, 0.4, 1),
            'color_diffuse': Vec(0.8, 0.8, 0.8, 1),
            'color_specular': Vec(1, 1, 1, 1),
        }
        renderable = Renderable(
            parent_node,
            mesh,
            shader,
            params,
            enable_light=True)

        super().__init__(renderable)

        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        self[Renderable].transform.translate(Vec(0.0, 0.0, 1.0))

    def update(self, dt):
        # NOTE: nothing to do
        pass
