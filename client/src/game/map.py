from game import Entity
from game.components import Renderable


class Map(Entity):
    """Map entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        TODO: add documentation.
        """
        mesh = resource['mesh']
        shader = resource['shader']

        renderable = Renderable(parent_node, mesh, shader)

        super().__init__(renderable)

    def update(self, dt):
        # NOTE: nothing to do
        pass
