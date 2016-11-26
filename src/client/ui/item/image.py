"""Image item module"""

from . import Item


class Image(Item):
    """Image item class

    Concrete implementation of items representing images.
    """

    def __init__(self, parent, **kwargs):
        """Constructor.

        FIXME: find a proper way to define images

        :param parent: The parent item
        :type parent: :class:`ui.item.Item`

        Keyword Arguments:
            * position (:class:`..util.point.Point`): The item position relative to
                the parent
            * width (:class:`int`): The item width
            * height (:class:`int`): The item height
            * anchor (:class:`.Anchor`): The item anchor override
            * margin (:class:`.Margin`): The item margin override
            * image (:class:`str`): The image
        """
        image = kwargs.pop('image', None)
        super().__init__(parent, **kwargs)
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
