from abc import ABC
from abc import abstractmethod
from itertools import count


class Entity(ABC):
    """Base classe for all game entities"""

    #: mapping of all the entities where the key is the entity id, and the value
    # is the entity itself
    ENTITIES = {}

    #: count iterator for incremental unique internal ids for each created
    # entity.
    count = count()

    def __init__(self, *components):
        """Constructor.

        :param components: List of components for this entity.
        :type components: sequence of :class:`game.component.Component`
        """
        self.e_id = next(self.count)
        self.ENTITIES[self.e_id] = self
        self._components = {}
        for comp in components:
            comp.entity = self
            self._components[type(comp)] = comp

    def __getitem__(self, key):
        """Item getter.

        Get the specified component from the entity. An entity can have at most
        a component of each type.

        :param key: The class of the component.
        :type key: :class:`game.component.Component`
        """
        return self._components[key]

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
