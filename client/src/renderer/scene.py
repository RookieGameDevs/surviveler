from abc import ABC
from abc import abstractmethod
from matlib import mat4


class Scene:
    """Visual scene which represents the tree of renderable objects.

    The scene has always a root node, to which all other nodes are attached, and
    is always rendered starting from root.
    """

    def __init__(self):
        self.root = RootNode()

    def render(self, rndr):
        """Render the scene using the given renderer.

        :param rndr: Renderer to use
        :type rndr: :class:`renderer.Renderer`
        """
        self.root.render(rndr, mat4())


class AbstractSceneNode(ABC):
    """Base class for scene nodes.

    A scene node is a renderable element in the scene tree, which can be a
    static geometry, character mesh, UI element and so on.

    Each node has a transformation associated to it, which is local to the node.
    During rendering, that transformation will be chained to those of parent
    nodes and in turn, will affect children nodes.
    """

    def __init__(self):
        self.children = []
        self.transform = mat4()

    @abstractmethod
    def render(self, rndr, transform):
        """Renders the node.

        This method should perform all rendering related calls, for which the
        passed computed transform should be used.

        :param rndr: Renderer to use.
        :type rndr: :class:`renderer.Renderer`

        :param transform: Node's computed transformation matrix. Not to be
            confused with `self.transform`, which describes node's local
            transformation.
        :type transform: :class:`numpy.ndarray`
        """
        pass

    def get_children(self):
        """Returns children nodes.

        :return: List of children nodes.
        :rtype: list
        """
        return self.children

    def add_child(self, node):
        """Add a node as child.

        :param node: Node instance to add as child.
        :type node: a class derived from :class:`renderer.scene.AbstractSceneNode`
        """
        self.children.append(node)

    def remove_child(self, node):
        """Remove a child node.

        :param node: Node instance to remove.
        :type node: a class derived from :class:`renderer.scene.AbstractSceneNode`
        """
        try:
            self.children.remove(node)
        except ValueError:
            pass


class RootNode(AbstractSceneNode):
    """A special node used as root for the scene tree, which `render()` method
    renders the entire tree and performs the parent-child transformations
    chaining.
    """

    def render(self, rndr, transform):

        def render_all(node, parent_transform):
            node.render(rndr, node.transform * parent_transform)

            for child in node.get_children():
                render_all(child, node.transform)

        for child in self.get_children():
            render_all(child, self.transform)


class GeometryNode(AbstractSceneNode):
    """A node for attaching static geometry (mesh) to the scene."""

    def __init__(self, mesh, shader, params=None):
        """Constructor.

        :param mesh: Instance of the mesh to render.
        :type mesh: :class:`renderer.Mesh`

        :param shader: Shader to use during rendering. At each render, the node
            will set the `transform` parameter (uniform) implicitly, all other
            parameters can be passed as `params` argument.
        :type shader: :class:`renderer.Shader`

        :param params: Additional shader parameters. These are passed to the
            shader verbatim.
        :type params: map
        """
        super(GeometryNode, self).__init__()
        self.mesh = mesh
        self.shader = shader
        self.params = params or {}

    def render(self, rndr, transform):
        self.params['transform'] = transform
        self.shader.use(self.params)
        self.mesh.render(rndr)
