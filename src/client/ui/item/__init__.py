"""The base item module"""
from .. import Anchor
from ..point import Point
from .binding import Binding
from abc import ABCMeta
from abc import abstractmethod
from collections import OrderedDict
from functools import partial


class ValidationError(Exception):
    """Exception class for validation errors"""


class Item(metaclass=ABCMeta):
    """The basic item class.

    All the user interface items will inherit this abstract item class.
    """

    def __init__(self, parent, **kwargs):
        """Constructor.

        :param parent: The parent item
        :type parent: :class:`Item`

        Keyword Arguments:
            * position (:class:`..point.Point`): The item position relative to
                the parent
            * width (:class:`int`): The item width
            * height (:class:`int`): The item height
            * anchor (:class:`..Anchor`): The item anchor override
            * margin (:class:`..Margin`): The item margin override
        """
        self.parent = parent
        self.children = OrderedDict()

        # Cached geometry properties
        self._position = None
        self._width = None
        self._height = None
        self._anchor = {}
        self._margin = {}

        # Source geometry properties
        #   1. Position relative to the parent item
        self._s_position = kwargs.get('position')
        #   2. Pre-defined width
        self._s_width = kwargs.get('width')
        #   3. Pre-defined height
        self._s_height = kwargs.get('height')
        #   4. Anchor
        self._s_anchor = kwargs.get('anchor')
        #   5. Margin
        self._s_margin = kwargs.get('margin')

        self.validate_item()

    def validate_item(self):
        """Check for missing positioning information.
        """
        # TODO: add documentation

        AT = Anchor.AnchorType

        def get(anchor, at):
            if anchor:
                return anchor.get(at)

        x_coord_available = any([
            self._s_position is not None,
            get(self._s_anchor, AT.left) is not None,
            get(self._s_anchor, AT.hcenter) is not None and self._s_width is not None,
            get(self._s_anchor, AT.right) is not None and self._s_width
        ])

        y_coord_available = any([
            self._s_position is not None,
            get(self._s_anchor, AT.top) is not None,
            get(self._s_anchor, AT.vcenter) is not None and self._s_height is not None,
            get(self._s_anchor, AT.bottom) is not None and self._s_height
        ])

        width_available = any([
            self._s_width is not None,
            get(self._s_anchor, AT.left) is not None and get(
                self._s_anchor, AT.right) is not None,
            get(self._s_anchor, AT.left) is not None and get(
                self._s_anchor, AT.hcenter) is not None,
            get(self._s_anchor, AT.hcenter) is not None and get(
                self._s_anchor, AT.right) is not None
        ])

        height_available = any([
            self._s_height is not None,
            get(self._s_anchor, AT.top) is not None and get(
                self._s_anchor, AT.bottom) is not None,
            get(self._s_anchor, AT.top) is not None and get(
                self._s_anchor, AT.vcenter) is not None,
            get(self._s_anchor, AT.vcenter) is not None and get(
                self._s_anchor, AT.bottom) is not None
        ])

        if not all([x_coord_available, y_coord_available, width_available, height_available]):
            raise ValidationError(
                'Not enough information for positioning and layouting')

    def bind_item(self):
        """Bind the item and trigger the binding of the child items.
        """
        # Calculate the values of the configured anchors
        if self._s_anchor is not None:
            self.calculate_anchor()

        # Calculate the width
        if self._s_width is not None:
            self._width = self._s_width
        else:
            self._width = self.calculate_width()

        # Calculate the height
        if self._s_height is not None:
            self._height = self._s_height
        else:
            self._height = self.calculate_height()

        # Calculate the position
        if self._s_position is not None:
            self._position = self._s_position + self.parent.position
        else:
            self._position = self.calculate_position()

        # Recalculate all the anchors with the internal data for caching purpose
        self._anchor = self.cache_anchor()

        for ref, item in self.children.items():
            item.bind_item()

    def calculate_anchor(self):
        """TODO: add documentation
        """
        ATget = Anchor.AnchorTarget
        # Mapping of targets with real items
        items = {
            ATget.parent: self.parent,
            ATget.sibling: self.parent.get_sibling(self)
        }

        self._anchor = {}
        for t, (target, tt) in self._s_anchor.items():
            self._anchor[t] = items[target].anchor[tt]

    def calculate_width(self):
        """TODO: add documentation
        """
        AT = Anchor.AnchorType
        width = 0
        if AT.left in self._anchor and AT.hcenter in self._anchor:
            width = (self._anchor[AT.hcenter] - self._anchor[AT.left]) * 2
        elif AT.left in self._anchor and AT.right in self._anchor:
            width = self._anchor[AT.right] - self._anchor[AT.left]
        elif AT.hcenter in self._anchor and AT.right in self._anchor:
            width = (self._anchor[AT.right] - self._anchor[AT.hcenter]) * 2
        return width

    def calculate_height(self):
        """TODO: add documentation
        """
        AT = Anchor.AnchorType
        height = 0
        if AT.top in self._anchor and AT.vcenter in self._anchor:
            height = (self._anchor[AT.vcenter] - self._anchor[AT.top]) * 2
        elif AT.top in self._anchor and AT.bottom in self._anchor:
            height = self._anchor[AT.bottom] - self._anchor[AT.top]
        elif AT.vcenter in self._anchor and AT.bottom in self._anchor:
            height = (self._anchor[AT.bottom] - self._anchor[AT.vcenter]) * 2
        return height

    def calculate_position(self):
        """TODO: add documentation
        """
        AT = Anchor.AnchorType

        x = y = 0

        if AT.left in self._anchor:
            x = self._anchor[AT.left]
        elif AT.hcenter in self._anchor:
            x = self._anchor[AT.hcenter] - int(self._width / 2)
        elif AT.right in self._anchor:
            x = self._anchor[AT.right] - self._width

        if AT.top in self._anchor:
            y = self._anchor[AT.top]
        elif AT.vcenter in self._anchor:
            y = self._anchor[AT.vcenter] - int(self._height / 2)
        elif AT.bottom in self._anchor:
            y = self._anchor[AT.bottom] - self._height

        return Point(x, y)

    def cache_anchor(self):
        AT = Anchor.AnchorType
        x = self._position.x
        y = self._position.y
        return {
            AT.left: x,
            AT.hcenter: x + int(self._width / 2),
            AT.right: x + self._width,
            AT.top: y,
            AT.vcenter: y + int(self._height / 2),
            AT.bottom: y + self._height,
        }

    @property
    def position(self):
        """TODO: add documentation
        """
        if self._position is not None:
            return self._position
        else:
            raise AttributeError

    @property
    def width(self):
        """TODO: add documentation
        """
        if self._width is not None:
            return self._width
        else:
            raise AttributeError

    @property
    def height(self):
        """TODO: add documentation
        """
        if self._height is not None:
            return self._height
        else:
            raise AttributeError

    @property
    def anchor(self):
        """TODO: add documentation
        """
        return self._anchor

    @property
    def margin(self):
        """TODO: add documentation
        """
        return self._margin

    def get_sibling(self, item):
        """Get a sibling.

        In case there are no siblings, the parent itself is returned.

        : param item: The item that are referring to the sibling.
        : type item:: class: `ui.item.Item`

        : returns: The sibling item(or the parent in case of no siblings)
        : rtype:: class: `ui.item.Item`
        """
        sibling = self
        for ref, child in self.children.items():
            if child == item:
                return sibling
            sibling = child

    def add_child(self, ref, item, **properties):
        """Attaches a child to the item, and binds the properties.

        : param ref: The name that identifies internally the child
        : type ref:: class: `str`

        : param item: The actual item to be added as child
        : type item:: class: `ui.item.Item`

        : param ** properties: A mapping of the properties to be bound
        : type ** properties: : class: `dict`
        """
        self.children[ref] = item

        for binding, prop in properties.items():
            getter = partial(getattr, self.children[ref], prop)
            setter = partial(setattr, self.children[ref], prop)
            print(binding, prop, repr(getter()))
            setattr(self, binding, Binding(getter, setter))

    @abstractmethod
    def update(self, dt):
        """Item update method.

        This method should be implemented by subclasses of Item. It describes
        the behavior the class should have during updates.

        : param dt: The time delta since last update(in seconds)
        : type dt:: class: `float`
        """
        pass
