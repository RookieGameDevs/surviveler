from context import Context
from events import subscriber
from game.entities.actor import ActorType
from game.entities.character import Character
from game.events import ActorSpawn
from matlib.vec import Vec
import logging


LOG = logging.getLogger(__name__)


class Player(Character):
    """Game entity representing the local player"""

    def update(self, dt):
        """Update the local player.

        This method computes player's game logic as a function of time and sends
        the appropriate event.

        :param dt: Time delta from last update.
        :type dt: float
        """
        super(Player, self).update(dt)

        # map player game position to world (x,y -> x,z)
        x, z = self.position

        # update camera position and orientation
        context = Context.get_instance()
        camera = context.camera
        camera.position = Vec(x, 20, z + 5)
        camera.look_at(camera.position, Vec(x, 0, z))


@subscriber(ActorSpawn)
def player_spawn(evt):
    """Instantiate and add the local player into the game.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorSpawn`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context

    # Only instantiate the player if it does not exist
    entity_exists = context.resolve_entity(evt.srv_id)

    # NOTE: check if the srv_id is exactly the player id received from the
    # server during the handshake.
    is_player = evt.srv_id == evt.context.player_id
    is_character = evt.actor_type in Character.MEMBERS

    if not entity_exists and is_character and is_player:
        # Search for the proper resource to use basing on the actor_type.
        # FIXME: right now it defaults on grunts.
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['entities_map'].get(
                ActorType(evt.actor_type).name,
                '/characters/grunt'))

        # Create the player
        player = Player(resource, context.scene, evt.actor_type)
        context.entities[player.e_id] = player
        context.server_entities_map[evt.srv_id] = player.e_id


@subscriber(ActorSpawn)
def player_spawn_sound(evt):
    # TODO: add documentation
    LOG.debug('Event subscriber: {}'.format(evt))
    is_player = evt.srv_id == evt.context.player_id
    if is_player:
        evt.context.audio_mgr.play_fx('toilet_flush')
