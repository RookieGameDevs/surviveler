from enum import IntEnum
from enum import unique
from events import subscriber
from game.components import Movable
from game.components import Renderable
from game.entities.entity import Entity
from game.entities.widgets.health_bar import HealthBar
from game.events import ActorIdle
from game.events import ActorMove
from game.events import ActorStatusChange
from math import atan
from math import copysign
from math import pi
from matlib import Vec
from renderer import Texture
from renderer.scene import SceneNode
from utils import to_scene
import logging


LOG = logging.getLogger(__name__)


WHOLE_ANGLE = 2.0 * pi


@unique
class ActorType(IntEnum):
    """Enumeration of the possible actors"""
    grunt = 0
    # TODO: enable these actors types when they will be available
    # programmer = 1
    engineer = 2
    zombie = 3


class Actor(Entity):
    """Game entity which represents an actor."""

    def __init__(self, resource, health, parent_node):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param health: The current amount of hp and the total one
        :type health: :class:`tuple`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        # Health is going to be a property used to update only when necessary
        # the health bar.
        self._health = health

        shader = resource['shader']
        mesh = resource['model']
        texture = Texture.from_image(resource['texture'])

        # shader params
        params = {
            'tex': texture,
        }

        # Initialize movable component
        movable = Movable((0.0, 0.0))

        # Setup the group node and add the health bar
        # FIXME: I don't like the idea of saving the group node here. We need
        # something better here.
        self.group_node = SceneNode()
        g_transform = self.group_node.transform
        g_transform.translate(to_scene(*movable.position))
        parent_node.add_child(self.group_node)

        self.health_bar = HealthBar(
            resource['health_bar'], health[0] / health[1], self.group_node,
            resource.data.get('hb_y_offset'))

        # create components
        renderable = Renderable(
            self.group_node,
            mesh,
            shader,
            params,
            textures=[texture],
            enable_light=True)

        # initialize actor
        super().__init__(renderable, movable)

        # FIXME: hardcoded bounding box
        self._bounding_box = Vec(-0.5, 0, -0.5), Vec(0.5, 2, 0.5)

        self.heading = 0.0
        # rotation speed = 2π / fps / desired_2π_rotation_time
        self.rot_speed = 2 * pi / 60 / 1.5

    @property
    def health(self):
        """Returns the health of the character as a tuple current/total.

        :returns: The health of the character
        :rtype: :class:`tuple`
        """
        return self._health

    @health.setter
    def health(self, value):
        """Sets the health of the character.

        Propagate the modification to the buliding health bar.

        :param value: The new health
        :type value: :class:`tuple`
        """
        self._health = value
        self.health_bar.value = value[0] / value[1]

    @property
    def position(self):
        """The position of the actor in world coordinates.

        :returns: The position
        :rtype: :class:`tuple`
        """
        return self[Movable].position

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

    def orientate(self):
        """Orientate the character towards the current destination.
        """
        direction = self[Movable].direction
        if direction:
            dx = direction.x
            dy = direction.y
            if dx:
                target_heading = atan(dy / dx) + (pi / 2) * copysign(1, dx)
            else:
                target_heading = pi if dy > 0 else 0

            # Compute remaining rotation
            delta = target_heading - self.heading
            abs_delta = abs(delta)
            if abs_delta > WHOLE_ANGLE / 2:
                abs_delta = WHOLE_ANGLE - abs(delta)
                delta = -delta

            if abs_delta < self.rot_speed * 2:
                # Rotation is complete within a small error.
                # Force it to the exact value:
                self.heading = target_heading
                return

            self.heading += copysign(1, delta) * self.rot_speed

            # normalize angle to be in (-pi, pi)
            if self.heading >= WHOLE_ANGLE / 2:
                self.heading = -WHOLE_ANGLE + self.heading
            if self.heading < -WHOLE_ANGLE / 2:
                self.heading = WHOLE_ANGLE + self.heading

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying character {}'.format(self.e_id))
        node = self.group_node
        node.parent.remove_child(node)

    def update(self, dt):
        """Update the character.

        This method computes character's game logic as a function of time.

        :param dt: Time delta from last update.
        :type dt: float
        """
        self[Movable].update(dt)
        x, y = self[Movable].position

        # FIXME: I don't like the idea of saving the group node here. We need
        # something better here.
        g_t = self.group_node.transform
        g_t.identity()
        g_t.translate(to_scene(x, y))

        t = self[Renderable].transform
        t.identity()
        t.rotate(Vec(0, 1, 0), -self.heading)

        self.orientate()

        # Update the health bar
        self.health_bar.update(dt)


@subscriber(ActorStatusChange)
def actor_health_change(evt):
    """Updates the number of hp of the actor.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map[evt.srv_id]
        actor = context.entities[e_id]
        actor.health = evt.new, actor.health[1]


@subscriber(ActorIdle)
def actor_set_postition(evt):
    """Updates the character position

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorIdle`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    actor = evt.context.resolve_entity(evt.srv_id)
    if actor:
        actor[Movable].position = evt.x, evt.y


@subscriber(ActorMove)
def character_set_movement(evt):
    """Set the move action in the actor.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorMove`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    actor = evt.context.resolve_entity(evt.srv_id)
    if actor and evt.path:
        actor[Movable].move(
            position=evt.position,
            path=evt.path,
            speed=evt.speed)