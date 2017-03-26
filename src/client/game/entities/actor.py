from enum import IntEnum
from enum import unique
from events import subscriber
from game.components import Movable
from game.entities.entity import Entity
from game.events import ActorActionChange
from game.events import ActorIdle
from game.events import ActorMove
from math import atan
from math import copysign
from math import pi
from matlib.vec import Vec
from renderlib.animation import AnimationInstance
from renderlib.material import Material
from renderlib.mesh import MeshProps
from renderlib.texture import Texture
from utils import to_scene
import logging


LOG = logging.getLogger(__name__)


WHOLE_ANGLE = 2.0 * pi


@unique
class ActorType(IntEnum):
    """Enumeration of the possible actors"""
    grunt = 0
    programmer = 1
    engineer = 2
    zombie = 3


@unique
class ActionType(IntEnum):
    """Enum of the various possible ActionType"""
    idle = 0
    move = 1
    build = 2
    repair = 3
    attack = 4
    drinking = 5


def action_anim_index(action_type):
    if action_type in {ActionType.idle, ActionType.drinking}:
        return 0
    elif action_type == ActionType.move:
        return 1
    else:
        return 2


class Actor(Entity):
    """Game entity which represents an actor."""

    # *FIXME* *FIXME* *FIXME*
    # REFACTOR THIS!!!
    TRANSFORMS = {
        ActorType.grunt: (pi, 0.12),
        ActorType.programmer: (pi, 0.022),
        ActorType.engineer: (pi, 5.5),
        ActorType.zombie: (pi, 0.05),
    }

    def init_animations(self, mesh):
        self.animations = {}
        for i in range(3):
            try:
                self.animations[i] = AnimationInstance(mesh.animations[i])
            except IndexError:
                self.animations[i] = None

    def __init__(self, resource, scene, actor_type):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param scene: Scene to add the actor to.
        :type scene: :class:`renderlib.scene.Scene`

        :param actor_type: Type of actor entity.
        :type actor_type: :enum:`game.entities.actor.ActorType`
        """
        self.resource = resource
        self.actor_type = actor_type

        mesh = resource['model']

        # root transformation to apply to the mesh
        self.transform = mesh.transform

        # instantiate animations
        self.init_animations(mesh)
        self.current_anim = self.animations[action_anim_index(ActionType.idle)]

        # create a 2D texture from texture image
        texture = Texture.from_image(resource['texture'], Texture.TextureType.texture_2d)

        # create a material
        material = Material()
        material.texture = texture
        material.receive_light = True

        # rendering props
        self.props = MeshProps()
        self.props.material = material
        self.props.animation = self.current_anim
        self.props.receive_shadows = True
        self.props.cast_shadows = True

        # add the mesh to the scene
        self.obj = scene.add_mesh(mesh, self.props)

        # Initialize movable component
        movable = Movable((0.0, 0.0))

        # initialize actor
        super().__init__(movable)

        # FIXME: hardcoded bounding box
        self._bounding_box = Vec(-0.5, 0, -0.5), Vec(0.5, 2, 0.5)

        self.heading = 0.0

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

            # tweak speed (XXX: make it more rational)
            rot_speed = abs_delta * 2 * pi / 40
            if abs_delta < rot_speed * 2:
                # Rotation is complete within a small error.
                # Force it to the exact value:
                self.heading = target_heading
                return

            self.heading += copysign(1, delta) * rot_speed

            # normalize angle to be in (-pi, pi)
            if self.heading >= WHOLE_ANGLE / 2:
                self.heading = -WHOLE_ANGLE + self.heading
            if self.heading < -WHOLE_ANGLE / 2:
                self.heading = WHOLE_ANGLE + self.heading

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying character {}'.format(self.e_id))

    def set_action(self, action_type):
        """Sets current player action.

        :param action_type: Action to set.
        :type action_type: :class:`game.entities.actor.ActionType`
        """
        anim = self.animations[action_anim_index(action_type)]
        self.props.animation = self.current_anim = anim

    def update(self, dt):
        """Update the character.

        This method computes character's game logic as a function of time.

        :param dt: Time delta from last update.
        :type dt: float
        """
        self[Movable].update(dt)
        x, y = self[Movable].position

        rot, scale = self.TRANSFORMS[self.actor_type]
        self.obj.position = to_scene(x, y)
        self.obj.rotation.rotatev(Vec(0, 1, 0), rot + -self.heading)
        self.obj.scale = Vec(scale, scale, scale)

        self.orientate()

        # play animation
        if self.current_anim:
            self.current_anim.play(dt)


def lookup_entity(evt):
    """Looks up the entity associated with given event.

    :param evt: Event object.
    :type evt: :class:`events.Event`
    """
    context = evt.context
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map[evt.srv_id]
        return context.entities[e_id]


@subscriber(ActorActionChange)
def actor_action_change(evt):
    """Updates actor action."""
    actor = lookup_entity(evt)
    if actor:
        actor.set_action(evt.new)


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
