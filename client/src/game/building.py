from enum import IntEnum
from enum import unique
from events import subscriber
from game import Entity
from game.components import Renderable
from game.events import BuildingDisappear
from game.events import BuildingSpawn
from matlib import Vec
from utils import to_scene
import logging


LOG = logging.getLogger(__name__)


@unique
class BuildingType(IntEnum):
    """Enumeration of the possible buildings"""
    mg_turret = 0


class Building(Entity):
    """Game entity which represents a building."""

    def __init__(self, resource, position, progress, completed, parent_node):
        """Constructor.

        :param resource: The building resource
        :type resource: :class:`loaders.Resource`

        :param position: The position of the building
        :type position: :class:`tuple`

        :param progress: The current amount of hp and the total one
        :type progress: :class:`tuple`

        :param completed: Whether the building is completed or not
        :type completed: :class:`bool`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        self.position = position
        self.progress = progress
        self.completed = completed

        shader = resource['shader']
        self.mesh_project = resource['model_project']
        self.mesh_complete = resource['model_complete']

        params = {
            'color_ambient': Vec(0.2, 0.2, 0.2, 1),
            'color_diffuse': Vec(0.6, 0.6, 0.6, 1),
            'color_specular': Vec(0.8, 0.8, 0.8, 1),
        }

        # create components
        renderable = Renderable(
            parent_node,
            self.mesh,
            shader,
            params,
            enable_light=True)

        t = renderable.transform
        t.translate(to_scene(*self.position))

        # initialize entity
        super().__init__(renderable)

    @property
    def mesh(self):
        """Return the appropriate mesh based on the building status.

        :returns: The appropriate mesh
        :rtype: :class:`renderer.Mesh`
        """
        if not self.completed:
            return self.mesh_project
        else:
            return self.mesh_complete

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying building {}'.format(self.e_id))
        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Update the building.

        Applies the status of the building in terms of shader params and meshes.

        :param dt: Time delta from last update.
        :type dt: float
        """
        node = self[Renderable].node
        node.mesh = self.mesh


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
        # FIXME: right now it defaults on mg_turret.
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['buildings_map'].get(
                BuildingType(evt.b_type).name,
                '/prefabs/buildings/mg_turret'
            )
        )

        # Create the building
        building = Building(
            resource, evt.pos, evt.progress, evt.completed, context.scene.root)
        context.entities[building.e_id] = building
        context.server_entities_map[evt.srv_id] = building.e_id

        # TODO: Change the walkable matrix here!


@subscriber(BuildingDisappear)
def building_disappear(evt):
    """Remove a building from the game.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map.pop(evt.srv_id)
        building = context.entities.pop(e_id)
        building.destroy()
