from events import Event


class EntitySpawn(Event):
    """An entity spawned on the scene.

    Event emitted when a new entity is discovered in the gamestate.
    """
    def __init__(self, srv_id, entity_type):
        self.srv_id = srv_id
        self.entity_type = entity_type

    def __str__(self):
        return '<EntitySpawn({}, {})>'.format(self.srv_id, self.entity_type)


class EntityDisappear(Event):
    """An entity disappeared from the scene.

    Event emitted when a previously existing entity does not exist anymore.
    """
    def __init__(self, srv_id):
        self.srv_id = srv_id

    def __str__(self):
        return '<EntityDisappear({})>'.format(self.srv_id)


class BuildingSpawn(Event):
    """A building spawned on the scene.

    Event emitted when a new building is discovered in the gamestate.
    """
    def __init__(self, srv_id, b_type, pos, progress, completed):
        self.srv_id = srv_id
        self.b_type = b_type
        self.pos = pos
        self.progress = progress
        self.completed = completed

    def __str__(self):
        return '<BuildingSpawn({}, {})>'.format(self.srv_id, self.b_type)


class BuildingDisappear(Event):
    """A building disappeared from the scene.

    Event emitted when a previously existing building does not exist anymore.
    """
    def __init__(self, srv_id, b_type, pos, progress, completed):
        self.srv_id = srv_id
        self.b_type = b_type
        self.pos = pos
        self.progress = progress
        self.completed = completed

    def __str__(self):
        return '<BuildingDisappear({}, {})>'.format(self.srv_id, self.b_type)


class BuildingStatusChange(Event):
    """A building has different status

    Event emitted when the amount of hp of a building changes.
    """
    def __init__(self, srv_id, old, new, completed):
        self.srv_id = srv_id
        self.old = old
        self.new = new
        self.completed = completed

    def __str__(self):
        return '<BuildingStatusChange({}, {}, {}, {})>'.format(
            self.srv_id, self.old, self.new, self.completed)


class TimeUpdate(Event):
    """Game time updated.

    Event emitted on game time change.
    """
    def __init__(self, hour, minute):
        """Constructor.

        :param hour: Hour.
        :type hour: int

        :param minute: Minute.
        :type minute: int
        """
        self.hour = hour
        self.minute = minute


class EntityPick(Event):
    """The player clicked on an entity.
    """
    def __init__(self, entity):
        """Constructor.

        :param entity: The game entity the player clicked on
        :type entity: :class:`game.entity.Entity`
        """
        self.entity = entity

    def __str__(self):
        return '<EntityPick({})>'.format(self.entity)


class EntityIdle(Event):
    """Entity is idle.

    Event emitted when the entity is in idle state.
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
    def __init__(self, srv_id, position, path, speed):
        """Constructor.

        :param srv_id: The server id of the entity.
        :type srv_id: int

        :param position: The current position.
        :type position: tuple

        :param path: List of coordinates which make up the current movement
            path.
        :type path: list

        :param speed: The player speed in game unit / seconds
        :type speed: float
        """
        self.srv_id = srv_id
        self.position = position
        self.path = path
        self.speed = speed

    def __str__(self):
        return '<EntityMove({}, {}, {}, {})>'.format(
            self.srv_id, self.position, self.path, self.speed)


class CharacterJoin(Event):
    """Character joined.

    Event emitted when a character joins the game.
    """
    def __init__(self, srv_id, name):
        self.srv_id = srv_id
        self.name = name

    def __str__(self):
        return '<CharacterJoin({}, {})>'.format(self.srv_id, self.name)


class CharacterLeave(Event):
    """Character left.

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
    """Local player joined.

    Event emitted when the local player actually joined the game.
    """

    def __str__(self):
        return '<PlayerJoin({}, {})>'.format(self.srv_id, self.name)


class GameModeChange(Event):
    """Game mode change.

    Event emitted when the game mode changed.
    """

    def __init__(self, prev, cur):
        self.prev, self.cur = prev, cur

    def __str__(self):
        return '<GameModeChange({}, {})>'.format(self.prev, self.cur)


class GameModeToggle(Event):
    """Game mode toggle.

    Event emitted when the user is toggling a game mode.
    """

    def __init__(self, mode):
        """Constructor.

        :param mode: The game mode we want to toggle
        :type mode: :enum:`context.Context.GameMode`
        """
        self.mode = mode

    def __str__(self):
        return '<GameModeToggle({})>'.format(self.mode)
