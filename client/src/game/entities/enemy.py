from events import subscriber
from game.entities.actor import Actor
from game.entities.actor import ActorType
from game.events import ActorDisappear
from game.events import ActorSpawn
from game.events import ActorStatusChange
from game.events import EntityPick
from network.message import Message
from network.message import MessageField as MF
from network.message import MessageType
import logging


LOG = logging.getLogger(__name__)


class Enemy(Actor):
    """Game entity which represents an enemy.
    """
    MEMBERS = {ActorType.zombie}


@subscriber(ActorSpawn)
def enemy_spawn(evt):
    """Add a enemy in the game.

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorSpawn`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context

    # Only instantiate the new character if it does not exist
    entity_exists = context.resolve_entity(evt.srv_id)

    if not entity_exists and evt.actor_type in Enemy.MEMBERS:
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['entities_map'].get(
                ActorType(evt.actor_type).name,
                '/enemies/zombie'
            )
        )

        tot = resource.data['tot_hp']

        # Create the character
        character = Enemy(resource, evt.actor_type, (evt.cur_hp, tot), context.scene.root)
        context.entities[character.e_id] = character
        context.server_entities_map[evt.srv_id] = character.e_id


@subscriber(ActorDisappear)
def enemy_disappear(evt):
    """Remove an enemy from the game.

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorDisappear`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    is_zombie = evt.actor_type in Enemy.MEMBERS
    if evt.srv_id in context.server_entities_map and is_zombie:
        e_id = context.server_entities_map.pop(evt.srv_id)
        character = context.entities.pop(e_id)
        character.destroy()


@subscriber(ActorDisappear)
def enemy_death_sound(evt):
    # TODO: add documentation
    is_zombie = evt.actor_type in Enemy.MEMBERS
    if is_zombie:
        evt.context.audio_mgr.play_fx('zombie_death')


@subscriber(EntityPick)
def enemy_click(evt):
    """Remove an enemy from the game.

    Gets all the relevant data from the event.

    :param evt: The event instance
    :type evt: :class:`game.events.ActorDisappear`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    if isinstance(evt.entity, Enemy):
        msg = Message(MessageType.attack, {
            MF.id: context.server_id(evt.entity.e_id),
        })
        context.msg_queue.append(msg)


@subscriber(ActorStatusChange)
def fight_sounds(evt):
    """Play zombie attack sounds.
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    is_zombie = evt.actor_type in Enemy.MEMBERS
    if evt.srv_id in context.server_entities_map and is_zombie:
        if evt.new < evt.old:
            evt.context.audio_mgr.play_fx('punch')
