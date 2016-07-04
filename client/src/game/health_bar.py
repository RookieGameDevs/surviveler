from game import Entity
from game.components import Renderable
from matlib import Vec
from renderer import Rect
from math import pi
import logging


LOG = logging.getLogger(__name__)


class HealthBar(Entity):
    """Game entity which represents a generic health bar."""

    def __init__(self, resource, value, parent_node):
        """Constructor.

        :param resource: The health bar resource
        :type resource: :class:`loaders.Resource`

        :param value: The percentage of health
        :type value: :class:`float`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        self._value = value

        self.w = resource.data['width']
        self.h = resource.data['height']
        y_offset = resource.data['y_offset']

        rect = Rect(self.w, self.h)

        shader = resource['shader']

        params = {
            'width': float(self.w),
            'height': float(self.h),
            'value': value * self.w,
        }

        renderable = Renderable(
            parent_node,
            rect,
            shader,
            params,
            enable_light=False)

        t = renderable.transform
        t.translate(Vec(-self.w / 2, y_offset, 0))
        t.rotate(Vec(1, 0, 0), pi / 2)

        super().__init__(renderable)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self[Renderable].node.params['value'] = v * self.w

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying health bar')
        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Update the health bar.

        :param dt: Time delta from last update.
        :type dt: float
        """
        pass
