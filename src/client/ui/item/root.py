from . import Item
from .. import Anchor
from ..util.point import Point


class RootItem(Item):
    """The root item.
    """

    def __init__(self, width, height):
        """Constructor.

        :param width: The screen width
        :type width: :class:`int`

        :param height: The screen height
        :type height: :class:`int`
        """
        super().__init__(self, position=Point(0, 0), width=width, height=height)

        # Root stays in 0, 0
        self._position = Point(0, 0)

        # Full width and height
        self._width = width
        self._height = height

        # No margins
        self._margin = {}

        # Anchor the root item to the whole window
        AT = Anchor.AnchorType
        self._anchor = {
            AT.left: 0,
            AT.hcenter: width / 2,
            AT.right: width,
            AT.top: 0,
            AT.vcenter: height / 2,
            AT.bottom: width,
        }

    def bind_item(self):
        """Just starts the binding on the child items.
        """
        for ref, item in self.children.items():
            item.bind_item()

    def update(self, dt):
        pass
