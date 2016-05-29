from game import Entity
from game.components import Renderable
from matlib import Vec
from renderer import Rect


WALKABLE = Vec(0, 1, 0)
NOT_WALKABLE = Vec(1, 0, 0)


class GridCell(Entity):
    def __init__(self, renderable, x, y, terrain):
        """Constructor.

        TODO: add documentation.
        """
        self.terrain = terrain
        self.x = x
        self.y = y

        renderable.transform.identity()
        renderable.transform.translate(Vec(x, y, 0))
        super().__init__(renderable)

        # Trigger a fake update event to set the color
        self[Renderable].node.params['color'] = (
            WALKABLE
            if self.terrain.is_walkable(self.x, self.y) else
            NOT_WALKABLE)

    def update(self, dt):
        pass


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, resource, parent_node,):
        """Constructor.

        :param resource: The terrain resource
        :type resource: :class:`loaders.Resource`

        :param parent_node: Parent node to attach the terrain entity to.
        :type param_node: subclass of :class:`renderer.SceneNode`
        """
        super().__init__()

        mesh = Rect(1, 1)
        shader = resource['shader']
        self.cells = []
        self.matrix = resource.data['matrix']

        for y, x_axis in enumerate(self.matrix):
            for x, walkable in enumerate(x_axis):
                renderable = Renderable(parent_node, mesh, shader)
                self.cells.append(GridCell(renderable, x, y, self))

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
