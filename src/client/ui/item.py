"""The base item module"""

from abc import ABCMeta
from abc import abstractmethod


class Item(metaclass=ABCMeta):
    """The basic item class.

    All the user interface components will inherit this abstract item class.
    """

    def __init__(self, parent=None, position=None, size=None, anchor=None, margin=None):
        """Constructor.

        :param parent: The parent item
        :type parent: :class:`ui.item.Item`

        :param position: The item position relative to the parent
        :type position: :class:`tuple`

        :param size: The position width and height
        :type size: :class:`tuple`

        :param anchor: The item anchor override
        :type anchor: :class:`ui.item.Anchor`

        :param margin: The item margin override
        :type margin: :class:`ui.item.Margin`
        """
        self.parent = parent
        self._position = position

        self.anchor = anchor if not position else None
        self.margin = margin if self.anchor else None

        self.size = size

    @property
    def position(self):
        """Returns the item position (top-left corner).

        How the position is computed:

          1. check if we have a parent component (otherwise the parent component
          is the whole screen)
          2. check if we have a position (this position is going to be relative
          to the parent component)
          3. if position is not available check for the anchor and compute the
          margin, returning the final position of the item.

        :returns: The item position.
        :rtype: :class:`tuple`
        """
        # FIXME: remove this hardcoded (0, 0)
        parent_position = self.parent.position if self.parent else (0, 0)
        if self._position:
            return parent_position + self._position
        else:
            # TODO: calculate the position using the anchor and margin
            pass

    @position.setter
    def position(self, pos):
        """Sets the item position (top-left corner).

        :param pos: The new position or None
        :type pos: :class:`tuple` or :class:`NoneType`
        """
        self._position = pos

    @property
    def width(self):
        """The width of the item.

        How the width is computed:

          1. check if there is an explicitly defined width
          2. in case of not explicitly defined width, check for a parent
          component
          3. check for the anchor, compute the margin and return the calculated
          width

        NOTE: in case there is no way to define the width of the item, the full
        width of the parent is used (applying the margin).

        FIXME: is int appropriate here?

        :returns: The item width.
        :rtype: :class:`int`
        """
        if self.size:
            return self.size[1]

        if self.anchor:
            # TODO: calculate the width using the anchor
            pass
        else:
            # TODO: take the width of the parent
            pass

        # TODO: apply margin and return the width

    @width.setter
    def width(self, pos):
        """Sets the width of the item.

        :param pos: The new width or None
        :type pos: :class:`tuple` or :class:`NoneType`
        """
        self.size[0] = pos

    @property
    def height(self):
        """The height of the item.

        How the height is computed:

          1. check if there is an explicitly defined height
          2. in case of not explicitly defined height, check for a parent
          component
          3. check for the anchor, compute the margin and return the calculated
          height

        NOTE: in case there is no way to define the height of the item, the full
        height of the parent is used (applying the margin).

        FIXME: is int appropriate here?

        :returns: The item height.
        :rtype: :class:`int`
        """
        if self.size:
            return self.size[1]

        if self.anchor:
            # TODO: calculate the height using the anchor
            pass
        else:
            # TODO: take the height of the parent
            pass

        # TODO: apply margin and return the height

    @height.setter
    def height(self, pos):
        """Sets the height of the item.

        :param pos: The new height or None
        :type pos: :class:`tuple` or :class:`NoneType`
        """
        self.size[1] = pos

    @abstractmethod
    def update(self, dt):
        """Item update method.

        This method should be implemented by subclasses of Item. It describes
        the behavior the class should have during updates.

        :param dt: The time delta since last update (in seconds)
        :type dt: :class:`float`
        """
        pass
