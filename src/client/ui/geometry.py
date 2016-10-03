"""Geometry: inner object handling geometry"""


class Geometry:
    """The geometry implementation.
    """

    def __init__(self, parent, position=None, size=None, anchor=None, margin=None):
        """Constructor.

        :param parent: The parent item
        :type parent: :class:`ui.geometry.Geometry`

        :param position: The item position relative to the parent
        :type position: :class:`tuple`

        :param size: The item width and height
        :type size: :class:`tuple`

        :param anchor: The anchor of the item the geometry is related to
        :type anchor: :class:`ui.Anchor`

        :param margin: The margin of the item the geometry is related to
        :type margin: :class:`ui.Margin`
        """
        self._position = position

        self.anchor = anchor if not position else None
        self.margin = margin if self.anchor else None

    @property
    def absolute_position(self):
        """Returns the item absolute position (top-left corner).

        How the position is computed:

          1. check if we have a parent item (otherwise the parent item is the
          whole screen)
          2. check if we have a position (this position is going to be relative
          to the parent item)
          3. if position is not available check for the anchor and compute the
          margin, returning the final position of the item.

        :returns: The item position.
        :rtype: :class:`tuple`
        """
        parent_position = (
            self.parent.absolute_position
            if self.parent
            # FIXME: remove this hardcoded (0, 0)
            else (0, 0)
        )

        return parent_position + self.position

    @property
    def position(self):
        """Returns the item position (top-left corner) relative to the parent.

        :returns: The item position relative to the parent.
        :rtype: :class:`tuple`
        """
        if self._position:
            self._position
        else:
            return (
                # TODO: this whole calculation is to be implemented
                (self.anchor.top + (self.margin.top or self.margin)),
                (self.anchor.left + (self.margin.left or self.margin)),
            )

    @property
    def width(self):
        """The width of the item.

        How the width is computed:

          1. check if there is an explicitly defined width
          2. in case of not explicitly defined width, check for a parent
          item
          3. check for the anchor, compute the margin and return the calculated
          width

        NOTE: in case there is no way to define the width of the item, the full
        width of the parent is used (applying the margin).

        FIXME: is int appropriate here?

        :returns: The item width.
        :rtype: :class:`int`
        """
        if self.size:
            return self.size[0]

        if self.anchor:
            # TODO: calculate the width using the anchor
            pass
        else:
            return self.parent.size[0]

        # TODO: apply margin and return the width

    @property
    def height(self):
        """The height of the item.

        How the height is computed:

          1. check if there is an explicitly defined height
          2. in case of not explicitly defined height, check for a parent
          item
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
            self.parent.size[1]

        # TODO: apply margin and return the height
