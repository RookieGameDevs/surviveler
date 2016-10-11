"""The user interface package"""
from enum import Enum


class Anchor(dict):
    """Represents the sets of anchors of a specified item.
    """

    class AnchorType(Enum):
        """Type of anchors.
        """
        top = 'top'
        left = 'left'
        bottom = 'bottom'
        right = 'right'
        vcenter = 'vcenter'
        hcenter = 'hcenter'

    class AnchorTarget(Enum):
        """Possible targets for anchors.
        """
        none = 'none'
        parent = 'parent'
        sibling = 'sibling'

    def __init__(self, **anchors):
        """Constructor.

        TODO: add documentation.
        """
        for a in Anchor.AnchorType:
            anc = anchors.get(a.name)
            if anc:
                target, t = anc.split('.')
                try:
                    target = Anchor.AnchorTarget(target)
                    t = Anchor.AnchorType(t)
                    self[a] = (target, t)
                except ValueError:
                    pass

    @classmethod
    def fill(cls):
        """Factory for fill-anchor.

        This is just a shortcut for an anchor that completely fills the parent.

        :returns: The generated fill anchor
        :rtype: :class:`Anchor`
        """
        return cls(
            left='parent.left',
            right='parent.right',
            top='parent.top',
            bottom='parent.bottom')

    @classmethod
    def center(cls):
        """Factory for center-anchor.

        This is just a shortcut for an anchor that puts the item in the center
        of the parent.

        :returns: The generated center anchor
        :rtype: :class:`Anchor`
        """
        return cls(vcenter='parent.vcenter', hcenter='parent.vcenter')


class Margin:
    """Represents the sets of margins of a specified item.
    """

    class MarginType(Enum):
        """Type of margins.
        """
        top = 'top'
        left = 'left'
        bottom = 'bottom'
        right = 'right'

    def __init__(self, margin=None, **margins):
        """Constructor.

        TODO: add documentation.
        """
        self.margin = margin
        for m in Margin.MarginType:
            setattr(self, m.name, margins.get(m.name, 0))


class UI:
    """Container of the whole UI.
    """

    def __init__(self):
        """Constructor.
        """
        self.ui = {}

    def push_item(self, data, parent, **overrides):
        """Creates a new item inspecting the resource and push it into the ui.

        :param data: The item data
        :type data: :class:`dict`

        :param parent: The parent item
        :type parent: :class:`type`

        :param **overrides: The overrides to apply to the item appearance
            definition.
        :type **overrides: :class:`dict`

        :returns: The id of the item
        :rtype: :class:`str`
        """
        # TODO: inspect for the proper type of the item and create it.
        pass

    def pop_item(self, item_id):
        """Pops the item identified by the provided id
        :param item_id: The item id
        :type item_id: :class:`ui.item.Item`
        """
        pass
