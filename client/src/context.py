class Context:
    """Game context.

    This object is passed along with each event and is modified in place when
    needed.
    """

    #: The context instance
    __INSTANCE = None

    def __init__(self, conf):
        """Constructor.

        :param conf: The game configuration
        :type conf: mapping
        """
        # Initialize the singleton instance
        Context.__INSTANCE = self

        self.conf = conf
        self.scene = None
        self.camera = None

        # Entity related maps
        self.server_entities_map = {}
        self.entities = {}

        # Local player entity information
        self.player_name = None
        self.player_id = None

        self.msg_queue = []

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

        :return: The entity object
        :rtype: :class:`game.entity.Entity`
        """
        return self.entities.get(self.server_entities_map.get(srv_id))

    def get_entity(self, e_id):
        """Returns the entity identified by the given (local) id.

        :param e_id: The local entity id
        :type e_id: int
        """
        return self.entities.get(e_id)
