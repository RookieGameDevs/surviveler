from enum import IntEnum
from enum import unique
from events import subscriber
from game import Entity
from game.components import Movable
from game.components import Renderable
from game.events import EntityDisappear
from game.events import EntityIdle
from game.events import EntityMove
from game.events import EntitySpawn
from game.events import EntityStatusChange
from game.health_bar import HealthBar
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
class EntityType(IntEnum):
    """Enumeration of the possible entities"""
    grunt = 0
    # TODO: enable these entity types when they will be available
    # programmer = 1
    engineer = 2
    zombie = 3


class Character(Entity):
    """Game entity which represents a character."""

    def __init__(self, resource, name, health, parent_node):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param name: Character's name.
        :type name: str

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
            'color_diffuse': Vec(0.2, 0.2, 0.2, 1),
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

        # initialize entity
        super().__init__(renderable, movable)

        self.name = name
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

    @property
    def position(self):
        """The position of the entity in world coordinates.

        :returns: The position
        :rtype: :class:`tuple`
        """
        return self[Movable].position

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying character {}'.format(self.e_id))
        node = self[Renderable].node
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


@subscriber(EntitySpawn)
def character_spawn(evt):
    """Add a character in the game.

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.EntitySpawn`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context

    # Only instantiate the new character if it does not exist
    entity_exists = context.resolve_entity(evt.srv_id)

    # NOTE: check if the srv_id is exactly the player id received from the
    # server during the handshake. And avoid spawing the character.
    is_player = evt.srv_id == evt.context.player_id

    if not entity_exists and not is_player:
        # Search for the proper resource to use basing on the entity_type.
        # FIXME: right now it defaults on zombies.
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['entities_map'].get(
                EntityType(evt.entity_type).name,
                '/enemies/zombie'
            )
        )

        # Search for the entity name
        name = context.players_name_map.get(evt.srv_id, '')
        # Create the entity
        character = Character(resource, name, evt.health, context.scene.root)
        context.entities[character.e_id] = character
        context.server_entities_map[evt.srv_id] = character.e_id


@subscriber(EntityDisappear)
def character_disappear(evt):
    """Remove a character from the game.

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.EntityDisappear`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map.pop(evt.srv_id)
        character = context.entities.pop(e_id)
        character.destroy()


@subscriber(EntityStatusChange)
def entity_health_change(evt):
    """Updates the number of hp of the entity.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map[evt.srv_id]
        entity = context.entities[e_id]
        entity.health = evt.new, entity.health[1]


@subscriber(EntityIdle)
def character_set_position(evt):
    """Updates the character position

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.EntityIdle`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    entity = evt.context.resolve_entity(evt.srv_id)
    if entity:
        entity[Movable].position = evt.x, evt.y


@subscriber(EntityMove)
def character_set_movement(evt):
    """Set the move action in the character entity.

    :param evt: The event instance
    :type evt: :class:`game.events.EntityMove`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    entity = evt.context.resolve_entity(evt.srv_id)
    if entity:
        entity[Movable].move(
            position=evt.position,
            path=evt.path,
            speed=evt.speed)
