from game import Entity
from game.components import Renderable
from matlib import Vec


class Map(Entity):
    """Map entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        TODO: add documentation.
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

    def update(self, dt):
        # NOTE: nothing to do
        pass
