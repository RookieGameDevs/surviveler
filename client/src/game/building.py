from enum import IntEnum
from enum import unique
from events import subscriber
from game import Entity
from game.components import Movable
from game.components import Renderable
from game.events import BuildingDisappear
from game.events import BuildingSpawn
from matlib import Vec
from network.message import MessageField as MF
from utils import to_scene
import logging


LOG = logging.getLogger(__name__)


@unique
class BuildingType(IntEnum):
    """Enumeration of the possible buildings"""
    barricade = 0


class Building(Entity):
    """Game entity which represents a building."""

    def __init__(self, resource, position, parent_node):
        """Constructor.

        :param resource: The building resource
        :type resource: :class:`loaders.Resource`

        :param position: The position of the building
        :type position: :class:`tuple`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        self.position = position

        shader = resource['shader']
        mesh = resource['model']

        # shader params
        params = {
            'color_ambient': Vec(0.0, 0.6, 0.2, 1),
            'color_diffuse': Vec(0.0, 0.8, 0.4, 1),
            'color_specular': Vec(1, 1, 1, 1),
        }

        # create components
        renderable = Renderable(
            parent_node,
            mesh,
            shader,
            params,
            enable_light=True)

        t = renderable.transform
        t.identity()
        t.translate(to_scene(*self.position))

        movable = Movable((0.0, 0.0))

        # initialize entity
        super().__init__(renderable, movable)

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying building {}'.format(self.e_id))
        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Update the building template.

        This method just applies the current position of the entity to the
        renderable transform.

        :param dt: Time delta from last update.
        :type dt: float
        """
        # TODO: update alpha based on the hit points
        params = {
            'color_ambient': Vec(0.0, 0.6, 0.2, 1),
            'color_diffuse': Vec(0.0, 0.8, 0.4, 1),
            'color_specular': Vec(1, 1, 1, 1),
        }

        self[Renderable].node.params = params


@subscriber(BuildingSpawn)
def building_spawn(evt):
    """Create a building.

    A building of the appropriate type is created and placed into the game.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context

    # Only instantiate the new building if it does not exist
    entity_exists = context.resolve_entity(evt.srv_id)

    if not entity_exists:
        # Search for the proper resource to use basing on the building_type.
        # FIXME: right now it defaults on barricade.
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['buildings_map'].get(
                BuildingType(evt.building_type).name,
                '/prefabs/buildings/barricade'
            )
        )

        # Create the building
        pos = (evt.building_data[MF.x_pos], evt.building_data[MF.y_pos])
        building = Building(resource, pos, context.scene.root)
        context.entities[building.e_id] = building
        context.server_entities_map[evt.srv_id] = building.e_id

        # TODO: Change the walkable matrix here!


@subscriber(BuildingDisappear)
def building_disappear(evt):
    """Remove a building from the game.
    """
    # TODO: Remove the building object
    # TODO: Change the walkable matrix appropriately
