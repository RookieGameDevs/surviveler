from events import send_event
from events import subscriber
from game.actions import place_building_template
from game.components import Renderable
from game.entities.actor import ActorType
from game.entities.building import BuildingType
from game.entities.entity import Entity
from game.events import BuildingDisappear
from game.events import BuildingSpawn
from game.events import GameModeChange
from game.events import GameModeToggle
from matlib.vec import Vec
from renderlib.core import Material
from renderlib.core import MeshRenderProps
from utils import in_matrix
from utils import to_matrix
from utils import to_scene
import logging

LOG = logging.getLogger(__name__)


class BuildingTemplate(Entity):
    """Game entity which represents a building template."""

    BUILDABLE_COLOR = Vec(0.0, 0.8, 0.4, 1)

    NON_BUILDABLE_COLOR = Vec(1, 0.0, 0.2, 1)

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

        mesh = resource['model_complete']

        # create material
        material = Material()
        material.color = self.BUILDABLE_COLOR

        # create render props container
        props = MeshRenderProps()
        props.material = material

        # create components
        renderable = Renderable(parent_node, mesh, props)

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
            self[Renderable].node.props.material.color = self.NON_BUILDABLE_COLOR
        else:
            self[Renderable].node.props.material.color = self.BUILDABLE_COLOR

        t = self[Renderable].transform
        t.ident()
        t.translatev(to_scene(x, y))
        t.scalev(Vec(1.05, 1.05, 1.05))


@subscriber(GameModeToggle)
def show_building_template(evt):
    """In case we are in a gamemode different from the default one shows the
    building template otherwise destroys it.
    """
    context = evt.context

    if evt.mode == context.GameMode.building:
        # Check if the player has the proper type and toggle the game mode.
        if context.character_type == ActorType.engineer:
            prev, cur = context.toggle_game_mode(evt.mode)
            send_event(GameModeChange(prev, cur))

    if context.game_mode == context.GameMode.building:
        # TODO: Remove the hardcoded building type with a dynamic one
        building_type = BuildingType.barricade.value
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['buildings_map'].get(
                BuildingType(building_type).name,
                '/prefabs/buildings/barricade'
            )
        )

        matrix, scale_factor = context.matrix, context.scale_factor
        building_template = BuildingTemplate(
            resource, matrix, scale_factor, context.scene.root)

        context.building_type = building_type
        context.building_template = building_template
        context.entities[building_template.e_id] = building_template
        x, y = context.input_mgr.mouse_position
        place_building_template(context, x, y)

    elif context.building_template is not None:
        # Reset the building-mode related context while exiting building mode
        context.building_type = 0
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


@subscriber(BuildingDisappear)
def set_cell_walkable(evt):
    """Set a cell as walkable in the debug terrain."""
    context = evt.context
    x, y = to_matrix(evt.pos[0], evt.pos[1], context.scale_factor)
    if in_matrix(context.matrix, x, y):
        context.matrix[y][x] = True
