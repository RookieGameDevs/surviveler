from events import Event


class PlayerPositionUpdated(Event):
    """Player position updated.

    Event emitted when the position of the Player changed.
    """
    def __init__(self, x, y):
        """Constructor.

        :param x: The position on x-axis.
        :type x: float

        :param y: The position on y-axis.
        :type y: float
        """
        self.x, self.y = x, y

    def __str__(self):
        return '<PlayerPositionUpdated({}, {})>'.format(self.x, self.y)


class PlayerActionMove(Event):
    """Receved move action.

    Event emitted whenever the player is subject to a move action.

    :param action: Move action payload.
    :type action: dict
    """
    def __init__(self, current_position, destination, speed):
        self.current_position = current_position
        self.destination = destination
        self.speed = speed

    def __str__(self):
        return '<PlayerActionMove({}, {}, {})>'.format(
            self.current_position, self.destination, self.speed)
