"""Utility binding class"""


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
