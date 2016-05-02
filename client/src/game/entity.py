from abc import ABC
from abc import abstractmethod
from itertools import count


class Entity(ABC):
    """Base classe for all game entities"""

    #: mapping of all the entities where the key is the entity id, and the value
    # is the entity itself
    ENTITIES = {}
    count = count()

    def __init__(self, *components):
        """Constructor.

        TODO: define the type of e_id

        :param e_id: The unique ideitifier of the entity.
        :type e_id: TBD.

        :param components: List of components for this entity.
        :type components: sequence of :class:`game.component.Component`
        """
        self.e_id = next(self.count)
        self.ENTITIES[self.e_id] = self
        self._components = {}
        for comp in components:
            self[type(comp)] = comp

    def __getitem__(self, key):
        return self._components[key]

    def __setitem__(self, key, value):
        """Sets the parent entity to the component while adding it"""
        value.entity = self
        self._components[key] = value

    @abstractmethod
    def update(self, dt):
        """Update function.

        :param dt: Time delta from last update.
        :type dt: float
        """
        pass

    @classmethod
    def get_entity(cls, e_id):
        """Class method that returns a registered entity (if exists).

        :param e_id: The unique ideitifier of the entity.
        :type e_id: TBD.
        """
        return cls.ENTITIES[e_id]
