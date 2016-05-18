from game import process_gamestate
from network import MessageField
from network import MessageType
from network import message_handler
from utils import as_utf8
from client.internal import Client as _Client
import logging


LOG = logging.getLogger(__name__)


class Client:
    """Client interface"""

    #: The instance of the client
    __INSTANCE = None

    def __init__(self, name, renderer, proxy, input_mgr, game_cfg):
        """Constructor.

        Just passes the arguments to the _Client constructor.

        :param name: The player name
        :type name: str

        :param renderer: The rederer
        :type renderer: :class:`renderer.Renderer`

        :param proxy: The message proxy
        :type proxy: :class:`network.message.MessageProxy`

        :param input_mgr: The input manager
        :type input_mgr: :class:`core.InputManager`

        :param game_cfg: Game configuration
        :type game_cfg: mapping
        """
        Client.__INSTANCE = self
        self.__client = _Client(renderer, proxy, input_mgr, game_cfg)
        self.__client.ping()
        self.__client.join(name)

        # Local player information
        self._player_name = name
        self._player_id = None

        self.server_entities_map = {}

    @classmethod
    def get_instance(cls):
        """Returns the instance of the clint (aka use client as a singleton)."""
        return cls.__INSTANCE

    #######################################
    # Wrappers around the internal client #
    #######################################

    def start(self):
        """Wraps the _Client start method."""
        self.__client.start()

    @property
    def delta(self):
        """The tstamp offset between client and server"""
        return self.__client.delta

    @property
    def proxy(self):
        """The message proxy."""
        return self.__client.proxy

    @property
    def scene(self):
        """The game scene."""
        return self.__client.scene

    @property
    def camera(self):
        """The camera."""
        return self.__client.camera

    @property
    def renderer(self):
        """The renderer."""
        return self.__client.renderer

    @property
    def config(self):
        """The game configuration."""
        return self.__client.game_cfg

    @property
    def player_id(self):
        return self._player_id

    @property
    def player(self):
        """Player entity."""
        if self.player_id is not None:
            return self.resolve_entity(self.player_id)
        return None

    ###########################
    # Public client interface #
    ###########################

    def get_entity(self, e_id):
        """Returns the entity object associated with the given entity id.

        :param e_id: The entity id.
        :type e_id: int

        :return: The required entity
        :rtype: :class:`game.Entity`
        """
        return self.__client.entities.get(e_id)

    def resolve_entity(self, srv_id):
        """Returns the entity object associated with given server-provided
        entity identifier.

        :param srv_id: The server entity id.
        :type srv_id: int

        :returns: The entity object, if any, `None` otherwise.
        :rtype: :class:`game.Entity`
        """
        e_id = self.server_entities_map.get(srv_id)
        return self.get_entity(e_id) if e_id is not None else None

    @message_handler(MessageType.pong)
    def pong(self, msg):
        """Just let the internal client handle the pong message"""
        self.__client.pong(msg)

    @message_handler(MessageType.stay)
    def handle_stay(self, msg):
        """Handles stay response from server.

        Assigns the client a server provided id, which uniquely identifies the
        controlled player entity.
        """
        self._player_id = msg.data[MessageField.id]
        LOG.info('Joined the party with ID {}'.format(self.player_id))
        # Add current player into the scene.
        e_id = self.__client.add_main_player(self._player_name)
        self.server_entities_map[self.player_id] = e_id
        LOG.info('Added local player "{}" with ID {}'.format(
            self._player_name, self.player_id))

        for srv_id, name in msg.data[MessageField.players].items():
            # TODO: remove me when the server is no more sending myself inside
            # the STAY payload.
            if srv_id == self.player_id:
                continue
            else:
                e_id = self.__client.add_player(name)
                LOG.info('Added existing player "{}" with ID {}'.format(
                    name, srv_id))
            self.server_entities_map[srv_id] = e_id

    @message_handler(MessageType.joined)
    def handle_joined(self, msg):
        """Handles player joins.

        Instantiates player entities and adds them to the game.
        """
        player_name = as_utf8(msg.data[MessageField.name])
        srv_id = msg.data[MessageField.id]
        if not self.resolve_entity(srv_id):
            # NOTE: only add players that are not already there.
            e_id = self.__client.add_player(player_name)
            self.server_entities_map[srv_id] = e_id
            LOG.info('Player "{}" joined with ID {}'.format(
                player_name, srv_id))

    @message_handler(MessageType.leave)
    def handle_leave(self, msg):
        srv_id = msg.data[MessageField.id]
        if srv_id == self.player_id:
            LOG.info('Local player disconnected')
            self.__client.exit()
        else:
            LOG.info('Player "{}" disconnected'.format(srv_id))
            e_id = self.server_entities_map.pop(srv_id)
            self.__client.remove_player(e_id)


@message_handler(MessageType.gamestate)
def gamestate_handler(client, msg):
    """Handle gamestate messages

    Handle the gamestate messages, actually spawning all the processors.

    Convert the server timestamp to the client one. Every timestamp in the
    gamestate messages payload from now on is to be considered comparable to
    the local timestamp (as returned by `utils.tstamp` function.

    :param client: the client interface instance
    :type client: :class:`client.Client`

    :param msg: the message to be processed
    :type msg: :class:`message.Message`
    """
    LOG.debug('Processing gamestate message')
    # Update the server timestamp adding the offset calculated after the
    # ping-pong exchange.
    msg.data[MessageField.timestamp] += client.delta or 0
    process_gamestate(msg.data)
