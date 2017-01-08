from context import Context
from events import subscriber
from game.entities.actor import Actor
from game.entities.actor import ActorType
from game.events import ActorDisappear
from game.events import ActorSpawn
from game.events import ActorStatusChange
from game.events import CharacterBuildingStart
from game.events import CharacterBuildingStop
from game.events import CharacterJoin
from matlib.vec import Vec
from renderer.scene import TextNode
from renderlib.core import TextRenderProps
from renderlib.font import Font
from renderlib.text import Text
import logging
import math


LOG = logging.getLogger(__name__)


class Label:
    """Object representing an on screen player label."""

    def __init__(self, resource, name, parent_node):
        """Constructor.

        :param resource: The label resource
        :type resource: :class:`loaders.Resource`

        :param name: The player name
        :type name: :class:`str`

        :param parent_node: The parent node
        :type parent_node: :class:`renderer.SceneNode`
        """
        context = Context.get_instance()

        font = resource['font'].get_size(14)
        text = Text(font, name)

        props = TextRenderProps()
        props.color = Vec(0.7, 0.7, 0.7, 0)

        self.node = parent_node.add_child(TextNode(text, props))

        self.ratio = context.ratio
        text_w = self.node.text.width
        self.translation = Vec(-text_w * context.ratio * 0.5, 3.5, 0)
        self.scale = Vec(context.ratio, context.ratio, context.ratio)

        t = self.node.transform
        t.translatev(self.translation)
        t.rotatev(Vec(1, 0, 0), math.pi / 2)
        t.scalev(self.scale)

    @property
    def text(self):
        """Returns the label text.

        :returns: The label text
        :rtype: :class:`str`
        """
        return self.node.text

    @text.setter
    def text(self, text):
        """Sets the label text.

        Also the transform is updated properly.

        :param text: The new text to be displayed
        :type text: :class:`str`
        """
        self.node.text = text

        text_w = self.node.width
        self.translation = Vec(-text_w * self.ratio * 0.5, 3.5, 0)
        self.scale = Vec(self.ratio, self.ratio, self.ratio)

        t = self.node.transform
        t.ident()
        t.translatev(self.translation)
        t.rotatev(Vec(1, 0, 0), math.pi / 2)
        t.scalev(self.scale)

    def update(self):
        """Update the rotation of the label to always be pointing to the camera.
        """
        context = Context.get_instance()
        c_pos = context.camera.position
        direction = Vec(c_pos.x, c_pos.y, c_pos.z, 1)
        direction.norm()
        z_axis = Vec(0, 0, 1)

        # Find the angle between the camera and the health bar, then rotate it.
        # NOTE: also scaling and tranlsation are applied here.
        angle = math.acos(z_axis.dot(direction))
        t = self.node.transform
        t.ident()
        t.translatev(self.translation)
        t.rotatev(Vec(1, 0, 0), angle)
        t.scalev(self.scale)


class Character(Actor):
    """Game entity which represents a character.
    """
    MEMBERS = {ActorType.grunt, ActorType.programmer, ActorType.engineer}

    def __init__(self, resource, actor_type, name, health, parent_node):
        """Constructor.

        :param resource: The character resource
        :type resource: :class:`loaders.Resource`

        :param health: The current amount of hp and the total one
        :type health: :class:`tuple`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        super().__init__(resource, actor_type, health, parent_node)

        self._name = name
        self.name_node = Label(resource, name, self.group_node)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        self.name_node.text.string = name

    def update(self, dt):
        super().update(dt)
        self.name_node.update()


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

        tot = resource.data['tot_hp']

        # Search for the character name
        name = context.players_name_map[evt.srv_id]
        # Create the character
        character = Character(
            resource, evt.actor_type, name, (evt.cur_hp, tot), context.scene.root)
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
        character.destroy()


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


@subscriber(CharacterJoin)
def set_character_name(evt):
    """Update the name of the character.

    :param evt: The event instance
    :type evt: :class:`game.events.CharacterJoin`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context
    entity = context.resolve_entity(evt.srv_id)
    if entity:
        entity.name = evt.name


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
