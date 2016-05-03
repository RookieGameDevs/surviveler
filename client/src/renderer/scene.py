from abc import ABC
from abc import abstractmethod
from matlib import Mat4


class SceneRenderContext:
    """Rendering context which is active during the current rendering pass."""

    def __init__(self, rndr, cam):
        """Constructor.

        :param rndr: Active renderer.
        :type rndr: :class:`renderer.Renderer`

        :param cam: Current camera.
        :type cam: :class:`renderer.Camera`
        """
        self._renderer = rndr
        self._camera = cam

    @property
    def renderer(self):
        """Active renderer."""
        return self._renderer

    @property
    def camera(self):
        """Camera to use."""
        return self._camera


class Scene:
    """Visual scene which represents the tree of renderable objects.

    The scene has always a root node, to which all other nodes are attached, and
    is always rendered starting from root.
    """

    def __init__(self):
        self.root = RootNode()

    def render(self, rndr, cam):
        """Render the scene using the given renderer.

        :param rndr: Renderer to use.
        :type rndr: :class:`renderer.Renderer`

        :param cam: Camera to use.
        :type cam: :class:`renderer.Camera`
        """
        ctx = SceneRenderContext(rndr, cam)
        self.root.render(ctx)


class AbstractSceneNode(ABC):
    """Base class for scene nodes.

    A scene node is a renderable element in the scene tree, which can be a
    static geometry, character mesh, UI element and so on.

    Each node has a transformation associated to it, which is local to the node.
    During rendering, that transformation will be chained to those of parent
    nodes and in turn, will affect children nodes.
    """

    def __init__(self):
        self._children = []
        self.transform = Mat4()

    @abstractmethod
    def render(self, ctx, transform):
        """Renders the node.

        This method should perform all rendering related calls, for which the
        passed computed transform should be used.

        :param ctx: Current render context.
        :type ctx: :class:`SceneRenderContext`

        :param transform: Node's computed transformation matrix. Not to be
            confused with `self.transform`, which describes node's local
            transformation.
        :type transform: :class:`matlib.Mat4`
        """
        pass

    @property
    def children(self):
        """List tof children nodes."""
        return self._children

    def add_child(self, node):
        """Add a node as child.

        :param node: Node instance to add as child.
        :type node: a class derived from :class:`renderer.scene.AbstractSceneNode`
        """
        self._children.append(node)

    def remove_child(self, node):
        """Remove a child node.

        :param node: Node instance to remove.
        :type node: a class derived from :class:`renderer.scene.AbstractSceneNode`
        """
        try:
            self._children.remove(node)
        except ValueError:
            pass


class RootNode(AbstractSceneNode):
    """A special node used as root for the scene tree, which `render()` method
    renders the entire tree and performs the parent-child transformations
    chaining.
    """

    def render(self, ctx, transform=None):

        def render_all(node, parent_transform):
            node.render(ctx, parent_transform * node.transform)

            for child in node.children:
                render_all(child, node.transform)

        for child in self.children:
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

    def render(self, ctx, transform):
        self.params['transform'] = transform
        self.params['projection'] = ctx.camera.transform
        self.shader.use(self.params)
        self.mesh.render(ctx.renderer)
