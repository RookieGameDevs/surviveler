from events import Event


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
