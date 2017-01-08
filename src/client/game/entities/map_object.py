from enum import IntEnum
from enum import unique
from events import subscriber
from game.components import Renderable
from game.entities.entity import Entity
from game.events import EntityPick
from game.events import ObjectSpawn
from math import pi
from matlib.vec import Vec
from network.message import Message
from network.message import MessageField as MF
from network.message import MessageType
from renderlib.core import Material
from renderlib.core import MeshRenderProps
from renderlib.texture import Texture
from utils import to_scene
import logging


Y_AXIS = Vec(0, 1, 0)


LOG = logging.getLogger(__name__)


@unique
class ObjectType(IntEnum):
    """Enumeration of the possible static objects"""
    coffee = 0


class MapObject(Entity):
    """Static object on the map."""

    def __init__(self, resource, parameters, parent_node):
        """Constructor.

        :param resource: Resource containing the object data.
        :type resource: :class:`resource_manager.Resource`

        :param parameters: Parameters for the object.
        :type parameters: :class:`dict`

        :param parent_node: Node to attach the object to.
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        mesh = resource['model']
        texture = Texture.from_image(
            resource['texture'],
            Texture.TextureType.texture_2d)

        material = Material()
        material.texture = texture

        props = MeshRenderProps()
        props.material = material

        renderable = Renderable(parent_node, mesh, props)

        super().__init__(renderable)

        self[Renderable].transform.translatev(
            to_scene(*parameters['pos']))

        if 'rotation' in parameters:
            self[Renderable].transform.rotatev(
                Y_AXIS, parameters['rotation'] * pi / 180)

        # FIXME: hardcoded bounding box
        self._position = parameters['pos']
        self._bounding_box = Vec(-0.5, 0.5, -0.5), Vec(0.5, 1.5, 0.5)

    def update(self, dt):
        # NOTE: nothing to do
        pass

    @property
    def bounding_box(self):
        l, m = self._bounding_box
        pos = self.position
        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        return l + Vec(pos[0], 0, pos[1] + 1), m + Vec(pos[0], 0, pos[1] + 1)

    @property
    def position(self):
        """The position of the actor in world coordinates.

        :returns: The position
        :rtype: :class:`tuple`
        """
        return self._position


@subscriber(ObjectSpawn)
def object_spawn(evt):
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    level = context.map

    map_resource = context.res_mgr.get('/map')
    obj_type = ObjectType(evt.obj_type)
    obj_res = map_resource[obj_type.name]
    obj_data = dict(
        {d['ref']: d for d in map_resource.data['usable_objects']}[obj_type.name],
        pos=evt.pos)

    map_obj = MapObject(obj_res, obj_data, level[Renderable].node)
    level.add_object(map_obj)

    context.entities[map_obj.e_id] = map_obj
    context.server_entities_map[evt.srv_id] = map_obj.e_id
    # TODO: handle operated objects


@subscriber(EntityPick)
def object_click(evt):
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if isinstance(evt.entity, MapObject):
        msg = Message(MessageType.use, {
            MF.id: context.server_id(evt.entity.e_id)
        })
        context.msg_queue.append(msg)
