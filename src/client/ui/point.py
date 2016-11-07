"""Definition of a basic 2d point class"""


class Point:
    """Basic 2d point implementation.
    """

    def __init__(self, x, y):
        """Constructor.

        For the purpose of the ui, x and y are both integers.

        :param x: The x-axis coordinate of the Point
        :type x: :class:`int`

        :param y: The y-axis coordinate of the Point
        :type y: :class:`int`
        """
        self._x, self._y = x, y

    def __add__(self, other):
        """Override of the + operator.

        :param other: The other point to be added
        :type other: :class:`Point`

        :returns: The resulting Point
        :rtype: :class:`Point`
        """
        return Point(self._x + other.x, self._y + other.y)

    def __radd__(self, other):
        """Override of the + operator (right).

        :param other: The other point to be added
        :type other: :class:`Point`

        :returns: The resulting Point
        :rtype: :class:`Point`
        """
        return self.__add__(other)

    def __iadd__(self, other):
        """Override of the += operator.

        :param other: The other point to be added
        :type other: :class:`Point`

        :returns: The point itself modified in place
        :rtype: :class:`Point`
        """
        self._x += other.x
        self._y += other.y
        return self

    def __eq__(self, other):
        """Override of the == operator.

        :param other: The other point to be checked
        :type other: :class:`Point`

        :returns: True if the point are equivalent
        :rtype: :class:`boo`
        """
        return self._x == other.x and self._y == other.y

    def __repr__(self):
        return 'Point({x}, {y})'.format(x=self._x, y=self._y)

    def __str__(self):
        return 'Point({x}, {y})'.format(x=self._x, y=self._y)

    @property
    def x(self):
        """Readonly x-axis coordinate

        :returns: The x-axis coordinate
        :rtype: :class:`int`
        """
        return self._x

    @property
    def y(self):
        """Readonly y-axis coordinate

        :returns: The y-axis coordinate
        :rtype: :class:`int`
        """
        return self._y
