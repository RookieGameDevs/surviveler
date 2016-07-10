from events import subscriber
from game.entities.actor import Actor
from game.entities.actor import ActorType
from game.events import ActorDisappear
from game.events import ActorSpawn
import logging


LOG = logging.getLogger(__name__)


class Enemy(Actor):
    MEMBERS = {ActorType.zombie}
    """Game entity which represents an enemy."""


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
        character = Enemy(resource, (evt.cur_hp, tot), context.scene.root)
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
    if evt.srv_id in context.server_entities_map:
        e_id = context.server_entities_map.pop(evt.srv_id)
        character = context.entities.pop(e_id)
        character.destroy()
