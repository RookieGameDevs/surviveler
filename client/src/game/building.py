from events import subscriber
from game import Entity
from game.components import Movable
from game.components import Renderable
from game.events import GameModeChange
from matlib import Vec
from utils import to_scene
import logging

LOG = logging.getLogger(__name__)


class Building(Entity):
    """Game entity which represents a building or a building template."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
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

        movable = Movable((0.0, 0.0))

        # initialize entity
        super().__init__(renderable, movable)

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying character {}'.format(self.e_id))
        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Update the building.

        This method just applies the current position of the entity to the
        renderable transform.

        :param dt: Time delta from last update.
        :type dt: float
        """
        self[Movable].update(dt)
        x, y = self[Movable].position

        t = self[Renderable].transform
        t.identity()
        t.translate(to_scene(x, y))


@subscriber(GameModeChange)
def show_building_template(evt):
    """In case we are in a gamemode different from the default one shows the
    building template otherwise destroies it.
    """
    context = evt.context
    if evt.cur == context.GameMode.building:
        resource = context.res_mgr.get('/prefabs/buildings/turret')
        building = Building(resource, context.scene.root)

        context.building_template = building
        context.entities[building.e_id] = building

    elif context.building_template is not None:
        bt, context.building_template = context.building_template, None
        del context.entities[bt.e_id]
        bt.destroy()
