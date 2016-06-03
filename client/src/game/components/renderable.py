from game.components import Component
from renderer import GeometryNode


class Renderable(Component):
    """Renderable component.

    Creates a new node on the scene graph and exposes the transform property of
    the node.
    """

    def __init__(self, parent_node, mesh, shader, params=None, textures=None,
            enable_light=False):
        """Constructor.

        :param parent_node: Parent node of the new game node.
        :type parent_node: :class:`renderer.scene.SceneNode`

        :param mesh: The mesh.
        :type mesh: :class:`renderer.Mesh`

        :param shader: The shader program.
        :type shader: :class:`renderer.Shader`

        :param params: The parameters mapping to pass during rendering to the
            shader program.
        :type params: mapping

        :param textures: Textures to apply to the mesh.
        :type textures: list of :class:`renderer.Texture`

        :param enable_light: Enable lighting for the renderable.
        :type enable_light: bool
        """
        self.entity = None
        self.node = GeometryNode(
            mesh,
            shader,
            params=params,
            textures=textures,
            enable_light=enable_light)
        parent_node.add_child(self.node)

    @property
    def transform(self):
        return self.node.transform

    @transform.setter
    def transform(self, value):
        self.node.transform = value
