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
        self._source_data = {
            'position': kwargs.get('position'),
            'width': kwargs.get('width'),
            'height': kwargs.get('height'),
            'anchor': kwargs.get('anchor'),
            'margin': kwargs.get('margin'),
        }

        self.validate_item()

    def validate_item(self):
        """Check for missing positioning information.
        """
        # TODO: add documentation

        AT = Anchor.AnchorType
        sd = self._source_data

        def get(anchor, at):
            if anchor:
                return anchor.get(at)

        x_coord_available = any([
            sd['position'] is not None,
            get(sd['anchor'], AT.left) is not None,
            get(sd['anchor'], AT.hcenter) is not None and sd['width'] is not None,
            get(sd['anchor'], AT.right) is not None and sd['width']
        ])

        y_coord_available = any([
            sd['position'] is not None,
            get(sd['anchor'], AT.top) is not None,
            get(sd['anchor'], AT.vcenter) is not None and sd['height'] is not None,
            get(sd['anchor'], AT.bottom) is not None and sd['height']
        ])

        width_available = any([
            sd['width'] is not None,
            get(sd['anchor'], AT.left) is not None and get(sd['anchor'], AT.right) is not None,
            get(sd['anchor'], AT.left) is not None and get(sd['anchor'], AT.hcenter) is not None,
            get(sd['anchor'], AT.hcenter) is not None and get(sd['anchor'], AT.right) is not None
        ])

        height_available = any([
            sd['height'] is not None,
            get(sd['anchor'], AT.top) is not None and get(sd['anchor'], AT.bottom) is not None,
            get(sd['anchor'], AT.top) is not None and get(sd['anchor'], AT.vcenter) is not None,
            get(sd['anchor'], AT.vcenter) is not None and get(sd['anchor'], AT.bottom) is not None
        ])

        if not all([x_coord_available, y_coord_available, width_available, height_available]):
            raise ValidationError('Not enough information for positioning and layouting')

    def bind_item(self):
        """Bind the item and trigger the binding of the child items.
        """
        sd = self._source_data

        # Calculate the values of the configured anchors
        if sd['anchor'] is not None:
            self.calculate_anchor()

        # Calculate the width
        if sd['width'] is not None:
            self._width = sd['width']
        else:
            self._width = self.calculate_width()

        # Calculate the height
        if sd['height'] is not None:
            self._height = sd['height']
        else:
            self._height = self.calculate_height()

        # Calculate the position
        if sd['position'] is not None:
            self._position = sd['position'] + self.parent.position
        else:
            self._position = self.calculate_position()

        # Recalculate all the anchors with the internal data for caching purpose
        self._anchor = self.cache_anchor()

        for ref, item in self.children.items():
            item.bind_item()

    def calculate_anchor(self):
        """TODO: add documentation
        """
        # Mapping of targets with real items
        self._anchor = {}
        for t, (target, tt) in self._source_data['anchor'].items():
            item = self.parent
            if target != 'parent':
                item = self.parent.get_child(target)
            self._anchor[t] = item.anchor[tt]

    def _calculate_dimension(self, *anchors):
        """TODO: add documentation
        """
        first, second, third = anchors

        dimension = 0
        if first in self._anchor and second in self._anchor:
            dimension = (self._anchor[second] - self._anchor[first]) * 2
        elif first in self._anchor and third in self._anchor:
            dimension = self._anchor[third] - self._anchor[first]
        elif second in self._anchor and third in self._anchor:
            dimension = (self._anchor[third] - self._anchor[second]) * 2
        return dimension

    def calculate_width(self):
        """TODO: add documentation
        """
        AT = Anchor.AnchorType
        return self._calculate_dimension(AT.left, AT.hcenter, AT.right)

    def calculate_height(self):
        """TODO: add documentation
        """
        AT = Anchor.AnchorType
        return self._calculate_dimension(AT.top, AT.vcenter, AT.bottom)

    def _calculate_coord(self, dimension, *anchors):
        """TODO: add documentation
        """
        first, second, third = anchors

        coord = 0
        if first in self._anchor:
            coord = self._anchor[first]
        elif second in self._anchor:
            coord = self._anchor[second] - int(dimension / 2)
        elif third in self._anchor:
            coord = self._anchor[third] - dimension

        return coord

    def calculate_position(self):
        """TODO: add documentation
        """
        AT = Anchor.AnchorType

        return Point(
            self._calculate_coord(self._width, AT.left, AT.hcenter, AT.right),
            self._calculate_coord(self._height, AT.top, AT.vcenter, AT.bottom))

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
        return self._position

    @property
    def width(self):
        """TODO: add documentation
        """
        return self._width

    @property
    def height(self):
        """TODO: add documentation
        """
        return self._height

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
