from game.components import Component
from renderer.scene import MeshNode


class Renderable(Component):
    """Renderable component.

    Creates a new node on the scene graph and exposes the transform property of
    the node.
    """

    def __init__(self, parent_node, mesh, props):
        """Constructor.

        :param mesh: The mesh.
        :type mesh: :class:`renderlib.mesh.Mesh`

        :param props: Mesh rendering properties container.
        :type props: :class:`renderlib.core.MeshRenderProps`
        """
        self.node = MeshNode(mesh, props)
        parent_node.add_child(self.node)

    @property
    def transform(self):
        return self.node.transform

    @transform.setter
    def transform(self, value):
        self.node.transform = value
