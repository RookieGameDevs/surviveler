from game import Entity
from game import Renderable
from game.events import PlayerPositionUpdated
from game.events import subscriber
from loaders import load_obj
from math import pi
from matlib import Mat4
from matlib import Vec3
from matlib import Y
from renderer import Mesh
from renderer import Shader
import logging


LOG = logging.getLogger(__name__)


WHOLE_ANGLE = 2.0 * pi


class Player(Entity):
    """Game entity which represents a player."""

    def __init__(self, parent_node):
        """Constructor.

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.AbstractSceneNode`
        """
        vertices, _, _, indices = load_obj('data/models/player.obj')
        mesh = Mesh(vertices, indices)
        shader = Shader.from_glsl(
            'data/shaders/simple.vert',
            'data/shaders/simple.frag')

        renderable = Renderable(parent_node, mesh, shader)
        super(Player, self).__init__(renderable)

        self.rot_angle = 0.0
        self.x = 0.0
        self.y = 0.0

    def update(self, dt):
        """Update the player.

        This method computes player's game logic as a function of time.

        :param dt: Time delta from last update.
        :type dt: float
        """
        self.rot_angle += dt * pi
        if self.rot_angle >= WHOLE_ANGLE:
            self.rot_angle -= WHOLE_ANGLE

        self[Renderable].transform = (
            Mat4.trans(Vec3(self.x, self.y, 0)) *
            Mat4.rot(Y, self.rot_angle))


@subscriber(PlayerPositionUpdated)
def update_player_position(evt):
    """Updates the player position

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.PlayerPositionUpdated`
    """
    LOG.debug('Event subscriber: {}'.format(evt))

    # FIXME: find a proper way to map server ids with internal ids
    player = Entity.get_entity(0)
    player.x, player.y = evt.x, evt.y
