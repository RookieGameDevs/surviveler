from context import Context
from game.components import Renderable
from game.entities.entity import Entity
from math import pi
from matlib.vec import Vec
from renderer.primitives import Rect
from renderlib.core import MeshRenderProps
import logging
import math


LOG = logging.getLogger(__name__)


class HealthBar(Entity):
    """Game entity which represents a generic health bar."""

    def __init__(self, resource, value, parent_node, y_offset=None):
        """Constructor.

        :param resource: The health bar resource
        :type resource: :class:`loaders.Resource`

        :param value: The percentage of health
        :type value: :class:`float`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`

        :param y_offset: The offset on y-axis in world coordinates (NOTE:
            defaults to the resource value
        :type y_offset: :class:`float`
        """
        self._value = float(value)

        self.w = resource.data['width']
        self.h = resource.data['height']
        self.y_offset = y_offset or resource.data['y_offset']

        mesh = resource.userdata.get('mesh')
        if not mesh:
            mesh = Rect(self.w, self.h)
            resource.userdata['mesh'] = mesh

        props = MeshRenderProps()
        props.color = Vec(0.2, 0.4, 1)

        renderable = Renderable(parent_node, mesh, props)

        t = renderable.transform
        t.translatev(Vec(-self.w / 2, self.y_offset, 0))
        t.rotatev(Vec(1, 0, 0), pi / 2)

        super().__init__(renderable)

    @property
    def value(self):
        """Returns the value [0,1] of that is currently displayed.

        :returns: The value of the health bar
        :rtype: :class:`float`
        """
        return self._value

    @value.setter
    def value(self, v):
        """Sets the value [0,1] to be displayed.

        :param v: The value of the health bar
        :type v: :class:`float`
        """
        self._value = float(v)
        self[Renderable].node.params['value'] = self._value

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying health bar')
        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Updates the health bar.

        :param dt: Time delta from last update.
        :type dt: float
        """
        context = Context.get_instance()
        c_pos = context.camera.position
        direction = Vec(c_pos.x, c_pos.y, c_pos.z, 1)
        direction.norm()
        z_axis = Vec(0, 0, 1)

        # Find the angle between the camera and the health bar, then rotate it.
        angle = math.acos(z_axis.dot(direction))
        t = self[Renderable].transform
        t.ident()
        t.translatev(Vec(-self.w / 2, self.y_offset, 0))
        t.rotatev(Vec(1, 0, 0), angle)
