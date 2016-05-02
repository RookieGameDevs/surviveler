from abc import ABC
from abc import abstractmethod
from itertools import count
from renderer import GeometryNode


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
        :type components: sequence of :class:`game.gametree.Component`
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


class Component(ABC):
    """Base class for all components"""

    @abstractmethod
    def __init__(self):
        pass


class Renderable(Component):
    """Renderable component.

    Creates a new node on the scene graph and exposes the transform property of
    the node.
    """

    def __init__(self, parent_node, mesh, shader):
        """Constructor.

        :param parent_node: Parent node of the new game node.
        :type parent_node: :class:`renderer.scene.AbstractSceneNode`

        :param mesh: The mesh.
        :type mesh: :class:`renderer.Mesh`

        :param shader: The shader program.
        :type shader: :class:`renderer.Shader`
        """
        self.entity = None
        self.node = GeometryNode(mesh, shader)
        parent_node.add_child(self.node)

    @property
    def transform(self):
        return self.node.transform

    @transform.setter
    def transform(self, value):
        self.node.transform = value
