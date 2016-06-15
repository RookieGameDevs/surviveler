from events import Event


class EntitySpawn(Event):
    """Handles entity spawning on the scene.

    Event emitted when a new entity is discovered in the gamestate.
    """
    def __init__(self, srv_id, entity_data):
        self.srv_id = srv_id
        self.entity_data = entity_data

    def __str__(self):
        return '<EntitySpawn({})>'.format(self.srv_id)


class EntityIdle(Event):
    """Player position updated.

    Event emitted when the position of the Player changed.
    """
    def __init__(self, srv_id, x, y):
        """Constructor.

        :param srv_id: The server id of the entity.
        :type srv_id: int

        :param x: The position on x-axis.
        :type x: float

        :param y: The position on y-axis.
        :type y: float
        """
        self.srv_id = srv_id
        self.x, self.y = x, y

    def __str__(self):
        return '<EntityIdle({}, {}, {})>'.format(self.srv_id, self.x, self.y)


class EntityMove(Event):
    """Receved move action.

    Event emitted whenever the player is subject to a move action.
    """
    def __init__(self, srv_id, position, destination, speed):
        """Constructor.

        :param srv_id: The server id of the entity.
        :type srv_id: int

        :param position: The current position.
        :type position: tuple

        :param destination: The destination position
        :type destination: tuple

        :param speed: The player speed in game unit / seconds
        :type speed: float
        """
        self.srv_id = srv_id
        self.position = position
        self.destination = destination
        self.speed = speed

    def __str__(self):
        return '<EntityMove({}, {}, {}, {})>'.format(
            self.srv_id, self.position, self.destination, self.speed)


class CharacterJoin(Event):
    """Handles character joining.

    Event emitted when a character joins the game.
    """
    def __init__(self, srv_id, name):
        self.srv_id = srv_id
        self.name = name

    def __str__(self):
        return '<CharacterJoin({}, {})>'.format(self.srv_id, self.name)


class CharacterLeave(Event):
    """Handles character leaving.

    Event emitted when a character leaves the game.
    """
    def __init__(self, srv_id, name, reason):
        self.srv_id = srv_id
        self.name = name
        self.reason = reason

    def __str__(self):
        return '<CharacterLeave({}, {}, {})>'.format(
            self.srv_id, self.name, self.reason)


class PlayerJoin(CharacterJoin):
    """Handles local player joining.

    Event emitted when the local player actually joined the game.
    """

    def __str__(self):
        return '<PlayerJoin({}, {})>'.format(self.srv_id, self.name)
