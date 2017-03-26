from events import subscriber
from game.entities.actor import Actor
from game.entities.actor import ActorType
from game.events import ActorDisappear
from game.events import ActorSpawn
from game.events import ActorStatusChange
from game.events import CharacterBuildingStart
from game.events import CharacterBuildingStop
import logging


LOG = logging.getLogger(__name__)


class Character(Actor):
    """Game entity which represents a character.
    """
    MEMBERS = {ActorType.grunt, ActorType.programmer, ActorType.engineer}

    def __init__(self, resource, scene, actor_type):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param scene: Scene to add the character bar to.
        :type scene: :class:`renderlib.scene.Scene`

        :param actor_type: Character actor type.
        :type actor_type: enum
        """
        super().__init__(resource, scene, actor_type)


@subscriber(ActorSpawn)
def character_spawn(evt):
    """Add a character in the game.

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorSpawn`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context

    # Only instantiate the new character if it does not exist
    entity_exists = context.resolve_entity(evt.srv_id)

    # NOTE: check if the srv_id is exactly the player id received from the
    # server during the handshake. And avoid spawing the character.
    is_player = evt.srv_id == evt.context.player_id
    is_character = evt.actor_type in Character.MEMBERS

    if not entity_exists and is_character and not is_player:
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['entities_map'].get(
                ActorType(evt.actor_type).name,
                '/enemies/grunt'
            )
        )

        # Create the character
        character = Character(
            resource, context.scene, evt.actor_type)
        context.entities[character.e_id] = character
        context.server_entities_map[evt.srv_id] = character.e_id


@subscriber(ActorDisappear)
def character_disappear(evt):
    """Remove a character from the game.

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorDisappear`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    is_character = evt.actor_type in Character.MEMBERS
    if evt.srv_id in context.server_entities_map and is_character:
        e_id = context.server_entities_map.pop(evt.srv_id)
        character = context.entities.pop(e_id)
        character.remove()


@subscriber(ActorDisappear)
def character_death_sound(evt):
    # TODO: add documentation
    is_character = evt.actor_type in Character.MEMBERS
    if is_character:
        evt.context.audio_mgr.play_fx('player_death')


@subscriber(ActorStatusChange)
def character_get_hit_sound(evt):
    """Play character attack sounds.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    is_character = evt.actor_type in Character.MEMBERS
    if evt.srv_id in context.server_entities_map and is_character:
        if evt.new < evt.old:
            evt.context.audio_mgr.play_fx('zombie_attack')


@subscriber(CharacterBuildingStart)
def character_building_start(evt):
    # TODO: add documentation
    LOG.debug('Event subscriber: {}'.format(evt))
    evt.context.audio_mgr.play_fx('crafting', loops=-1, key=evt.srv_id)


@subscriber(CharacterBuildingStop)
def character_building_stop(evt):
    # TODO: add documentation
    LOG.debug('Event subscriber: {}'.format(evt))
    evt.context.audio_mgr.stop_fx(key=evt.srv_id)
