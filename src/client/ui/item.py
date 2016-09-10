"""The base item module"""

from abc import ABCMeta
from abc import abstractmethod
from collections import OrderedDict
from functools import partial


class Binding:
    """Descriptor protocol implementation for bound properties.
    """

    def __init__(self, getter, setter=None, deleter=None):
        """Constructor.

        :param getter: The getter fuction
        :type getter: :class:`function`

        :param setter: The setter function
        :type setter: :class:`function`

        :param deleter: The deleter function
        :type deleter: :class:`function`
        """
        self.getter = getter
        self.setter = setter
        self.deleter = deleter

    # Implementation of the Descriptor protocol
    def __get__(self, obj, objtype=None):
        return self.getter()

    def __set__(self, obj, value):
        if self.setter:
            return self.setter(value)

    def __delete__(self, obj):
        if self.deleter:
            return self.deleter()


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

        self.children = OrderedDict()

    def __getattribute__(self, name):
        """Override of the standard __getattribute__ method.

        This override is needed for runtime property binding.

        This method is used to check if the required item conform to the
        Descriptor protocol and in case use it to get the actual value.

        :param name: The name of the attribute
        :type name: :class:`str`
        """
        value = super().__getattribute__(name)
        if hasattr(value, '__get__'):
            value = value.__get__(self, self.__class__)
        return value

    def __setattr__(self, name, value):
        """Override of the standard __setattr__ method.

        This override is needed for runtime property binding.

        This method is used to check if the required item conform to the
        Descriptor protocol and in case use it to set the new value.

        :param name: The name of the attribute
        :type name: :class:`str`

        :param value: The new value for the bound property
        :type value: type of the bound property
        """
        try:
            obj = super().__getattribute__(name)
        except AttributeError:
            pass
        else:
            if hasattr(obj, '__set__'):
                return obj.__set__(self, value)
        return super().__setattr__(name, value)

    def addChild(self, ref, item, **properties):
        """Attaches a child to the item, and binds the properties.

        :param ref: The name that identifies internally the child
        :type ref: :class:`str`

        :param item: The actual item to be added as child
        :type item: :class:`ui.item.Item`

        :param **properties: A mapping of the properties to be bound
        :type **properties: :class:`dict`
        """
        self.children[ref] = item

        for binding, prop in properties.items():
            getter = partial(getattr, self.children[ref], prop)
            setter = partial(setattr, self.children[ref], prop)
            print(binding, prop, repr(getter()))
            setattr(self, binding, Binding(getter, setter))

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
