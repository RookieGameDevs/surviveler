"""Image item module"""

from .item import Item


class Image(Item):
    """Image item class

    Concrete implementation of items representing images.
    """

    def __init__(
            self,
            parent=None, position=None, size=None, anchor=None, margin=None,
            image=None):
        """Constructor.

        FIXME: find a proper way to define images.

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

        :param image: The image
        :type image: :class:`str`
        """
        super().__init__(parent, position, size, anchor, margin)
        self._image = image

    @property
    def image(self):
        """Returns the image.

        :returns: The image
        :rtype: :class:`str`
        """
        return self._image

    @image.setter
    def image(self, image):
        """Sets the image.

        :param image: The new image
        :type image: :class:`str`
        """
        self._image = image

    def update(self, dt):
        """Image update method.

        NOTE: this is a noop

        :param dt: The time delta since last update (in seconds)
        :type dt: :class:`float`
        """
        pass
