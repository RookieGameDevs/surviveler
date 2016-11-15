"""The base item module"""
from .. import Anchor
from .. import Margin
from ..point import Point
from abc import ABCMeta
from abc import abstractmethod
from collections import OrderedDict


class ValidationError(Exception):
    """Exception class for validation errors"""


def validate_item(source_data):
    """Check for missing positioning information.

    This method validates the positioning information of the item.

    For an item to be valid the following conditions need to be true:
        * available x coordinate (directly or via anchor)
        * available y coordinate (directly or via anchor)
        * width available (directly or via anchor)
        * height available (directly or via anchor)
        * not conflicting information for width and height

    This method just does static validation: eventual conflicts due to
    circular dependencies will be validated at binding time.

    In case of validation error a ValidationError is raised.

    :param source_data: The original source data
    :type source_data: :class:`dict`

    :returns: The validated source data
    :rtype: :class:`dict`
    """
    AT = Anchor.AnchorType
    sd = source_data

    def get(anchor, at):
        if anchor:
            return anchor.get(at)

    # For the x coordinate to be considered defined the item needs to:
    # 1. have a defined position
    # 2. have the left anchor defined
    # 3. have the horizontal center and the width defined
    # 4. have the right anchor and the width defined
    x_available = any([
        sd['position'] is not None,
        get(sd['anchor'], AT.left) is not None,
        get(sd['anchor'], AT.hcenter) is not None and sd['width'] is not None,
        get(sd['anchor'], AT.right) is not None and sd['width']
    ])

    # For the y coordinate to be considered defined the item needs to:
    # 1. have a defined position
    # 2. have the top anchor defined
    # 3. have the vertical center and the height defined
    # 4. have the bottom anchor and the height defined
    y_available = any([
        sd['position'] is not None,
        get(sd['anchor'], AT.top) is not None,
        get(sd['anchor'], AT.vcenter) is not None and sd['height'] is not None,
        get(sd['anchor'], AT.bottom) is not None and sd['height']
    ])

    # For the width to be considered defined the item needs to:
    # 1. have a defined width
    # 2. have at least two horizontal anchors defined
    w_available = any([
        sd['width'] is not None,
        get(sd['anchor'], AT.left) is not None and get(sd['anchor'], AT.right) is not None,
        get(sd['anchor'], AT.left) is not None and get(sd['anchor'], AT.hcenter) is not None,
        get(sd['anchor'], AT.hcenter) is not None and get(sd['anchor'], AT.right) is not None
    ])

    # For the height to be considered defined the item needs to:
    # 1. have a defined height
    # 2. have at least two vertical anchors defined
    h_available = any([
        sd['height'] is not None,
        get(sd['anchor'], AT.top) is not None and get(sd['anchor'], AT.bottom) is not None,
        get(sd['anchor'], AT.top) is not None and get(sd['anchor'], AT.vcenter) is not None,
        get(sd['anchor'], AT.vcenter) is not None and get(sd['anchor'], AT.bottom) is not None
    ])

    # Assert that we are not having width conflicting information:
    # 1. No specified width
    # 2. Specified width and no more than one horizontal anchor value
    non_conflicting_w = (
        sd['width'] is None or
        len(list(filter(lambda x: get(sd['anchor'], x), [AT.left, AT.hcenter, AT.right]))) <= 1)

    # Assert that we are not having height conflicting information:
    # 1. No specified height
    # 2. Specified height and no more than one vertical anchor value
    non_conflicting_h = (
        sd['height'] is None or
        len(list(filter(lambda x: get(sd['anchor'], x), [AT.top, AT.vcenter, AT.bottom]))) <= 1)

    if not all([x_available, y_available, w_available, h_available, non_conflicting_w, non_conflicting_h]):
        raise ValidationError('Not enough information for positioning and layouting')

    return sd


def calculate_dimension(anchor, *anchors):
    """Calculate height or width, based on the relevant anchor values.

    As relevant anchor values we consider both:
        * [left, hcenter, right] -> width
        * [top, vcenter, bottom] -> height

    :param anchor: The anchor values
    :type anchor: :class:`dict`

    :param *anchors: List of relevant anchor values
    :type *anchors: :class:`list`

    :returns: The dimension
    :rtype: :class:`int`
    """
    first, second, third = anchors

    dimension = 0
    if first in anchor and second in anchor:
        dimension = (anchor[second] - anchor[first]) * 2
    elif first in anchor and third in anchor:
        dimension = anchor[third] - anchor[first]
    elif second in anchor and third in anchor:
        dimension = (anchor[third] - anchor[second]) * 2
    return dimension


def calculate_coord(dimension, anchor, *anchors):
    """Calculate coordinate using the relevant size and anchor values.ABCMeta

    As relevant anchor values we consider both:
        * width, [left, hcenter, right] -> x
        * height, [top, vcenter, bottom] -> y

    :param dimension: The relevant dimension
    :type dimension: :class:`int`

    :param anchor: The anchor values
    :type anchor: :class:`dict`

    :param *anchors: List of relevant anchor values
    :type *anchors: :class:`list`

    :returns: The coordinate value
    :rtype: :class:`int`
    """
    first, second, third = anchors

    coord = 0
    if first in anchor:
        coord = anchor[first]
    elif second in anchor:
        coord = anchor[second] - int(dimension / 2)
    elif third in anchor:
        coord = anchor[third] - dimension

    return coord


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
        self._source_data = validate_item({
            'position': kwargs.get('position'),
            'width': kwargs.get('width'),
            'height': kwargs.get('height'),
            'anchor': kwargs.get('anchor'),
            # Margin defaults to 0
            'margin': kwargs.get('margin', Margin.null()),
        })

    def bind_item(self):
        """Bind the item and trigger the binding of the child items.

        The binding process is made of the following steps:
            1. Calculating the available anchor values (based on the relations).
            2. Calculating width and height (if not available).
            3. Calculation the position (if not available).
            4. Cache all the anchor values.
            5. Call the binding on all the children items.

        TODO: add dynamic checks on dependencies.
        """
        sd = self._source_data

        # Calculate the values of the configured margins
        self._margin = self.calculate_margin()

        # Calculate the values of the configured anchors
        if sd['anchor'] is not None:
            self._anchor = self.calculate_anchor()

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

        # Call the bind method on each children item
        for ref, item in self.children.items():
            item.bind_item()

    def calculate_margin(self):
        """Calculate the margin values.ABCMeta

        Simply fills the source data provided margins with 0s.ABCMeta

        :returns: The margin values
        :rtype: :class:`dict`
        """
        margin = {}
        for m in Margin.MarginType:
            margin[m] = self._source_data['margin'].get(m, 0)
        return margin

    def calculate_anchor(self):
        """Calculate the anchor values.

        Uses the source anchor to calculate the anchor values for each available
        reference.

        :returns: The anchor values
        :rtype: :class:`dict`
        """
        MT = Margin.MarginType

        # Mapping of targets with real items
        anchor = {}
        for t, (target, tt) in self._source_data['anchor'].items():
            item = self.parent
            if target != 'parent':
                item = self.parent.get_child(target)
            try:
                mt = MT(tt.value)
                margin = self._margin[mt]
                if mt in {MT.right, MT.bottom}:
                    margin = -margin
            except ValueError:
                margin = 0
            anchor[t] = item.anchor[tt] + margin
        return anchor

    def calculate_width(self):
        """Calculate the width using the anchor values.

        :returns: The width
        :rtype: :class:`int`
        """
        AT = Anchor.AnchorType
        return calculate_dimension(self._anchor, AT.left, AT.hcenter, AT.right)

    def calculate_height(self):
        """Calculate the height using the anchor values.

        :returns: The height
        :rtype: :class:`int`
        """
        AT = Anchor.AnchorType
        return calculate_dimension(self._anchor, AT.top, AT.vcenter, AT.bottom)

    def calculate_position(self):
        """Calculate the position using the available information.

        :returns: The position
        :rtype: :class:`..Point`
        """
        AT = Anchor.AnchorType

        return Point(
            calculate_coord(self._width, self._anchor, AT.left, AT.hcenter, AT.right),
            calculate_coord(self._height, self._anchor, AT.top, AT.vcenter, AT.bottom))

    def cache_anchor(self):
        """Cache all the anchor values.

        The cached anchor values are not going to be modified until a new bind
        operation is called.

        :returns: The anchor values
        :rtype: :class:`dict`
        """
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
        """Readonly top-left position of the item.

        :returns: The position of the Item
        :rtype: :class:`..Point`
        """
        return self._position

    @property
    def width(self):
        """Readonly width of the item.

        :returns: The width of the item
        :rtype: :class:`..Point`
        """
        return self._width

    @property
    def height(self):
        """Readonly height of the item.

        :returns: The height of the item
        :rtype: :class:`..Point`
        """
        return self._height

    @property
    def anchor(self):
        """Readonly anchor values of the item.

        :returns: The anchor values
        :rtype: :class:`dict`
        """
        return self._anchor

    @property
    def margin(self):
        """Readonly margin values of the item

        :returns: The margin values
        :rtype: :class:`dict`
        """
        return self._margin

    def add_child(self, ref, item):
        """Attaches a child to the item, and binds the properties.

        :param ref: The name that identifies internally the child
        :type ref: :class:`str`

        :param item: The actual item to be added as child
        :type item: :class:`ui.item.Item`
        """
        self.children[ref] = item

    @abstractmethod
    def update(self, dt):
        """Item update method.

        This method should be implemented by subclasses of Item. It describes
        the behavior the class should have during updates.

        :param dt: The time delta since last update(in seconds)
        :type dt: :class:`float`
        """
        pass
