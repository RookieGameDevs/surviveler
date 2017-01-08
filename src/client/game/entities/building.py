from enum import IntEnum
from enum import unique
from events import subscriber
from game.components import Renderable
from game.entities.entity import Entity
from game.entities.widgets.health_bar import HealthBar
from game.events import BuildingDisappear
from game.events import BuildingSpawn
from game.events import BuildingStatusChange
from game.events import EntityPick
from matlib.vec import Vec
from network.message import Message
from network.message import MessageField as MF
from network.message import MessageType
from renderer.scene import SceneNode
from renderlib.core import Material
from renderlib.core import MeshRenderProps
from renderlib.texture import Texture
from utils import to_scene
import logging


LOG = logging.getLogger(__name__)


@unique
class BuildingType(IntEnum):
    """Enumeration of the possible buildings"""
    barricade = 0
    mg_turret = 1


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
        self._position = position
        # Progress is going to be a property used to update only when necessary
        # the health bar.
        self._progress = progress
        self.completed = completed

        # create texture
        texture = Texture.from_image(
            resource['texture'],
            Texture.TextureType.texture_2d)
        self.mesh_project = resource['model_project']
        self.mesh_complete = resource['model_complete']

        # create material
        material = Material()
        material.texture = texture

        # create render props
        props = MeshRenderProps()
        props.material = material

        # Setup the group node and add the health bar
        group_node = SceneNode()
        g_transform = group_node.transform
        g_transform.translatev(to_scene(*position))
        parent_node.add_child(group_node)

        self.health_bar = HealthBar(
            resource['health_bar'], progress[0] / progress[1], group_node)


        # create components
        renderable = Renderable(group_node, self.mesh, props)

        # initialize entity
        super().__init__(renderable)

        # FIXME: hardcoded bounding box
        self._bounding_box = Vec(-0.5, 0, -0.5), Vec(0.5, 2, 0.5)

    @property
    def mesh(self):
        """Returns the appropriate mesh based on the building status.

        :returns: The appropriate mesh
        :rtype: :class:`renderer.Mesh`
        """
        if not self.completed:
            return self.mesh_project
        else:
            return self.mesh_complete

    @property
    def progress(self):
        """Returns the progress of the building as a tuple current/total.

        :returns: The progress of the building
        :rtype: :class:`tuple`
        """
        return self._progress

    @progress.setter
    def progress(self, value):
        """Sets the progress of the building.

        Propagate the modification to the buliding health bar.

        :param value: The new progress
        :type value: :class:`tuple`
        """
        self._progress = value
        self.health_bar.value = value[0] / value[1]

    @property
    def position(self):
        """The position of the entity in world coordinates.

        :returns: The position
        :rtype: :class:`tuple`
        """
        return self._position

    @property
    def bounding_box(self):
        """The bounding box of the entity.

        The bounding box is represented by the smaller and bigger edge of the box
        itself.

        :returns: The bounding box of the actor
        :rtype: :class:`tuple`
        """
        l, m = self._bounding_box
        pos = self.position
        return l + Vec(pos[0], 0, pos[1]), m + Vec(pos[0], 0, pos[1])

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying building {}'.format(self.e_id))

        # Destroys the health bar first.
        self.health_bar.destroy()

        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Updates the building.

        Applies the status of the building in terms of shader params and meshes.

        :param dt: Time delta from last update.
        :type dt: float
        """
        node = self[Renderable].node
        node.mesh = self.mesh

        # Update the health bar
        self.health_bar.update(dt)


@subscriber(BuildingSpawn)
def building_spawn(evt):
    """Creates a building.

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
                '/prefabs/buildings/barricade'
            )
        )

        tot = resource.data['tot_hp']
        # Create the building
        building = Building(
            resource, evt.pos, (evt.cur_hp, tot), evt.completed,
            context.scene.root)
        context.entities[building.e_id] = building
        context.server_entities_map[evt.srv_id] = building.e_id


@subscriber(BuildingDisappear)
def building_disappear(evt):
    """Removes a building from the game.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map.pop(evt.srv_id)
        building = context.entities.pop(e_id)
        building.destroy()


@subscriber(BuildingStatusChange)
def building_health_change(evt):
    """Updates the number of hp of the building.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map[evt.srv_id]
        building = context.entities[e_id]
        building.progress = evt.new, building.progress[1]
        building.completed = evt.completed


@subscriber(EntityPick)
def building_click(evt):
    """Check if the object picked is a building and if it needs repairing.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if isinstance(evt.entity, Building):
        msg = Message(MessageType.repair, {
            MF.id: context.server_id(evt.entity.e_id),
        })
        context.msg_queue.append(msg)
