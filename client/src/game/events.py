from events import Event


class ActorSpawn(Event):
    """An actor spawned on the scene.

    Event emitted when a new actor is discovered in the gamestate.
    """
    def __init__(self, srv_id, actor_type, cur_hp):
        self.srv_id = srv_id
        self.actor_type = actor_type
        self.cur_hp = cur_hp

    def __str__(self):
        return '<ActorSpawn({}, {}, {})>'.format(
            self.srv_id, self.actor_type, self.cur_hp)


class ActorDisappear(Event):
    """An actor disappeared from the scene.

    Event emitted when a previously existing actor does not exist anymore.
    """
    def __init__(self, srv_id):
        self.srv_id = srv_id

    def __str__(self):
        return '<ActorDisappear({})>'.format(self.srv_id)


class ActorStatusChange(Event):
    """A building has different status

    Event emitted when the amount of hp of a building changes.
    """
    def __init__(self, srv_id, old, new):
        self.srv_id = srv_id
        self.old = old
        self.new = new

    def __str__(self):
        return '<ActorStatusChange({}, {}, {})>'.format(
            self.srv_id, self.old, self.new)


class BuildingSpawn(Event):
    """A building spawned on the scene.

    Event emitted when a new building is discovered in the gamestate.
    """
    def __init__(self, srv_id, b_type, pos, cur_hp, completed):
        self.srv_id = srv_id
        self.b_type = b_type
        self.pos = pos
        self.cur_hp = cur_hp
        self.completed = completed

    def __str__(self):
        return '<BuildingSpawn({}, {})>'.format(self.srv_id, self.b_type)


class BuildingDisappear(Event):
    """A building disappeared from the scene.

    Event emitted when a previously existing building does not exist anymore.
    """
    def __init__(self, srv_id, b_type, pos, cur_hp, completed):
        self.srv_id = srv_id
        self.b_type = b_type
        self.pos = pos
        self.cur_hp = cur_hp
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
        :type entity: :class:`game.entities.entity.Entity`
        """
        self.entity = entity

    def __str__(self):
        return '<EntityPick({})>'.format(self.entity)


class ActorIdle(Event):
    """Actor is idle.

    Event emitted when the actor is in idle state.
    """
    def __init__(self, srv_id, x, y):
        """Constructor.

        :param srv_id: The server id of the actor.
        :type srv_id: int

        :param x: The position on x-axis.
        :type x: float

        :param y: The position on y-axis.
        :type y: float
        """
        self.srv_id = srv_id
        self.x, self.y = x, y

    def __str__(self):
        return '<ActorIdle({}, {}, {})>'.format(self.srv_id, self.x, self.y)


class ActorMove(Event):
    """Receved move action.

    Event emitted whenever the player is subject to a move action.
    """
    def __init__(self, srv_id, position, path, speed):
        """Constructor.

        :param srv_id: The server id of the actor.
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
        return '<ActorMove({}, {}, {}, {})>'.format(
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


class CharacterBuildingStart(Event):
    """Character started building.

    Event emitted when a character started building.
    """
    def __init__(self, srv_id):
        self.srv_id = srv_id

    def __str__(self):
        return '<CharacterBuildingStart({})>'.format(self.srv_id)


class CharacterBuildingStop(Event):
    """Character stopped building.

    Event emitted when a character stopped building.
    """
    def __init__(self, srv_id):
        self.srv_id = srv_id

    def __str__(self):
        return '<CharacterBuildingStop({})>'.format(self.srv_id)


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
