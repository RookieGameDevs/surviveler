from events import subscriber
from game.entities.actor import Actor
from game.entities.actor import ActorType
from game.events import EntityDisappear
from game.events import EntitySpawn
import logging


LOG = logging.getLogger(__name__)


class Character(Actor):
    """Game entity which represents a character."""
    def __init__(self, resource, name, health, parent_node):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param health: The current amount of hp and the total one
        :type health: :class:`tuple`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        super().__init__(resource, health, parent_node)

        self.name = name


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
        # Search for the proper resource to use basing on the character type.
        # FIXME: right now it defaults on zombies.
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['entities_map'].get(
                ActorType(evt.entity_type).name,
                '/enemies/zombie'
            )
        )

        tot = resource.data['tot_hp']

        # Search for the character name
        name = context.players_name_map.get(evt.srv_id, '')
        # Create the character
        character = Character(
            resource, name, (evt.cur_hp, tot), context.scene.root)
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
