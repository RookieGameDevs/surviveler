from enum import IntEnum
from enum import unique
from events import subscriber
from game.entities.entity import Entity
from game.events import BuildingDisappear
from game.events import BuildingSpawn
from game.events import BuildingStatusChange
from game.events import EntityPick
from matlib.vec import Vec
from network.message import Message
from network.message import MessageField as MF
from network.message import MessageType
from renderlib.material import Material
from renderlib.mesh import MeshProps
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

    def __init__(self, resource, scene, position, progress, completed):
        """Constructor.

        :param resource: The building resource
        :type resource: :class:`loaders.Resource`

        :param scene: Scene to add the building bar to.
        :type scene: :class:`renderlib.scene.Scene`

        :param position: The position of the building
        :type position: :class:`tuple`

        :param progress: The current amount of hp and the total one
        :type progress: :class:`tuple`

        :param completed: Whether the building is completed or not
        :type completed: :class:`bool`
        """
        super().__init__()

        self.scene = scene
        self.obj = None
        self._position = to_scene(*position)
        self._completed = None

        # create texture
        texture = Texture.from_image(resource['texture'], Texture.TextureType.texture_2d)
        self.mesh_project = resource['model_project']
        self.mesh_complete = resource['model_complete']

        # create material
        material = Material()
        material.texture = texture

        # create render props
        self.props = MeshProps()
        self.props.material = material

        # set initial building status
        self.completed = completed

        # FIXME: hardcoded bounding box
        self._bounding_box = Vec(-0.5, 0, -0.5), Vec(0.5, 2, 0.5)

    @property
    def position(self):
        return self._position

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, status):
        if status != self._completed:
            if self.obj:
                self.obj.remove()
            self.obj = self.scene.add_mesh(
                self.mesh_complete if status else self.mesh_project,
                self.props)
            self.obj.position = self.position
        self._completed = status

    @property
    def bounding_box(self):
        """The bounding box of the entity.

        The bounding box is represented by the smaller and bigger edge of the box
        itself.

        :returns: The bounding box of the actor
        :rtype: :class:`tuple`
        """
        l, m = self._bounding_box
        return l + self.position, m + self.position

    def remove(self):
        """Removes itself from the scene.
        """
        LOG.debug('Remove building {}'.format(self.e_id))
        self.obj.remove()

    def update(self, dt):
        """Updates the building.

        :param dt: Time delta from last update.
        :type dt: float
        """
        # NOTE: nothing to do
        pass


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
            resource, context.scene, evt.pos, (evt.cur_hp, tot), evt.completed)
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
        building.remove()


@subscriber(BuildingStatusChange)
def building_health_change(evt):
    """Updates the number of hp of the building.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map[evt.srv_id]
        building = context.entities[e_id]
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
