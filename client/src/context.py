from enum import Enum
from enum import unique


class Context:
    """Game context.

    This object is passed along with each event and is modified in place when
    needed.
    """

    #: The context instance
    __INSTANCE = None

    @unique
    class GameMode(Enum):
        """Enumerations of the game modes"""
        default = 'Default Mode'
        building = 'Building Mode'

    def __init__(self, conf):
        """Constructor.

        :param conf: The game configuration
        :type conf: mapping
        """
        # Initialize the singleton instance
        Context.__INSTANCE = self

        self.conf = conf
        self.input_mgr = None
        self.res_mgr = None
        self.matrix = None
        self.scale_factor = 1
        self.scene = None
        self.camera = None
        self.terrain = None
        self.ui = None

        # Entity related maps
        self.server_entities_map = {}
        self.entities = {}

        # Local player entity information
        self.player_name = None
        self.player_type = None
        self.player_id = None
        self.players_name_map = {}

        self.msg_queue = []

        # Game mode
        self.game_mode = Context.GameMode.default

        # Building template
        self.building_template = None

    @classmethod
    def get_instance(cls):
        """Gets the instance (if exists) of the context.
        """
        return cls.__INSTANCE

    @property
    def player(self):
        return self.resolve_entity(self.player_id)

    def resolve_entity(self, srv_id):
        """Resolve the srv_id into the local id of the entity.

        :param srv_id: The server id
        :type srv_id: int

        :returns: The entity object
        :rtype: :class:`game.entity.Entity`
        """
        return self.entities.get(self.server_entities_map.get(srv_id))

    def get_entity(self, e_id):
        """Returns the entity identified by the given (local) id.

        :param e_id: The local entity id
        :type e_id: int
        """
        return self.entities.get(e_id)

    def toggle_game_mode(self, mode=None):
        """Handle the game mode.

        In case the game mode is default: enter into the new game mode. In case
        the game mode is exactly the specified one, return to default mode.

        :param mode: The game mode to be toggled.
        :type mode: :enum:`context.GameMode`
        """
        mode = mode or Context.GameMode.default
        if self.game_mode == mode:
            prev, self.game_mode = self.game_mode, Context.GameMode.default
        else:
            prev, self.game_mode = self.game_mode, mode
        return prev, self.game_mode
