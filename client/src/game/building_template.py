from events import send_event
from events import subscriber
from game.actions import place_building_template
from game.character import EntityType
from game.components import Renderable
from game.entity import Entity
from game.events import BuildingDisappear
from game.events import BuildingSpawn
from game.events import GameModeChange
from game.events import GameModeToggle
from matlib import Vec
from utils import in_matrix
from utils import to_matrix
from utils import to_scene
import logging

LOG = logging.getLogger(__name__)


class BuildingTemplate(Entity):
    """Game entity which represents a building template."""

    BUILDABLE_COLOR = {
        'color_ambient': Vec(0.0, 0.6, 0.2, 1),
        'color_diffuse': Vec(0.0, 0.8, 0.4, 1),
    }

    NON_BUILDABLE_COLOR = {
        'color_ambient': Vec(0.8, 0.0, 0.1, 1),
        'color_diffuse': Vec(1, 0.0, 0.2, 1),
    }

    def __init__(self, resource, matrix, scale_factor, parent_node):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param matrix: The walkable matrix
        :type matrix: :class:`loaders.Resource`

        :param scale_factor: The scale factor of the grid.
        :type scale_factor: int

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        self.pos = (0, 0)
        self.matrix = matrix
        self.scale_factor = scale_factor

        shader = resource['shader']
        mesh = resource['model_complete']

        # shader params
        params = dict({
            'color_specular': Vec(1, 1, 1, 1),
        }, **self.BUILDABLE_COLOR)

        # create components
        renderable = Renderable(
            parent_node,
            mesh,
            shader,
            params,
            enable_light=True)

        # initialize entity
        super().__init__(renderable)

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying building template {}'.format(self.e_id))
        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Update the building template.

        This method just applies the current position of the entity to the
        renderable transform.

        :param dt: Time delta from last update.
        :type dt: float
        """
        x, y = self.pos

        m_x, m_y = to_matrix(x, y, self.scale_factor)
        if not in_matrix(self.matrix, m_x, m_y) or not self.matrix[m_y][m_x]:
            self[Renderable].node.params.update(self.NON_BUILDABLE_COLOR)
        else:
            self[Renderable].node.params.update(self.BUILDABLE_COLOR)

        t = self[Renderable].transform
        t.identity()
        t.translate(to_scene(x, y))
        t.scale(Vec(1.05, 1.05, 1.05))


@subscriber(GameModeToggle)
def show_building_template(evt):
    """In case we are in a gamemode different from the default one shows the
    building template otherwise destroys it.
    """
    context = evt.context

    if evt.mode == context.GameMode.building:
        # Check if the player has the proper type and toggle the game mode.
        if context.player_type == EntityType.engineer:
            prev, cur = context.toggle_game_mode(evt.mode)
            send_event(GameModeChange(prev, cur))

    if context.game_mode == context.GameMode.building:
        # TODO: load the proper resource based on the building type
        resource = context.res_mgr.get('/prefabs/buildings/mg_turret')
        matrix, scale_factor = context.matrix, context.scale_factor
        building_template = BuildingTemplate(resource, matrix, scale_factor, context.scene.root)

        context.building_template = building_template
        context.entities[building_template.e_id] = building_template
        x, y = context.input_mgr.mouse_position
        place_building_template(context, x, y)

    elif context.building_template is not None:
        bt, context.building_template = context.building_template, None
        del context.entities[bt.e_id]
        bt.destroy()


@subscriber(BuildingSpawn)
def set_cell_unwalkable(evt):
    """Set a cell as non-walkable in the debug terrain."""
    context = evt.context
    x, y = to_matrix(evt.pos[0], evt.pos[1], context.scale_factor)
    if in_matrix(context.matrix, x, y):
        context.matrix[y][x] = False
        context.terrain.set_walkable_state(context.matrix)


@subscriber(BuildingDisappear)
def set_cell_walkable(evt):
    """Set a cell as walkable in the debug terrain."""
    context = evt.context
    x, y = to_matrix(evt.pos[0], evt.pos[1], context.scale_factor)
    if in_matrix(context.matrix, x, y):
        context.matrix[y][x] = True
        context.terrain.set_walkable_state(context.matrix)
