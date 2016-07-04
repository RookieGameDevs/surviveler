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
        self.value = value

        w = resource.data['width']
        h = resource.data['height']
        y_offset = resource.data['y_offset']

        rect = Rect(w, h)

        shader = resource['shader']

        params = {
            'width': float(w),
            'height': float(h),
            'value': self.value * w,
        }

        renderable = Renderable(
            parent_node,
            rect,
            shader,
            params,
            enable_light=False)

        t = renderable.transform
        t.translate(Vec(-w / 2, y_offset, 0))
        t.rotate(Vec(1, 0, 0), pi / 2)

        super().__init__(renderable)

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
        self[Renderable].node.params['value'] = self.value
