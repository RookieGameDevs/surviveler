from matlib.mat import Mat
from renderlib.core import render_mesh
from renderlib.core import render_quad
from renderlib.core import render_text


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
        self._modelview_t = cam.modelview
        self._projection_t = cam.projection
        self._view = cam.projection * cam.modelview

    @property
    def renderer(self):
        """Active renderer."""
        return self._renderer

    @property
    def camera(self):
        """Camera to use."""
        return self._camera

    @property
    def modelview(self):
        """Computed model-view transformation matrix."""
        return self._modelview_t

    @property
    def projection(self):
        """Computed projection transformation matrix."""
        return self._projection_t

    @property
    def view(self):
        """Combined projection and model view matrix."""
        return self._view


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


class SceneNode:
    """Base class for scene nodes.

    A scene node is a renderable element in the scene tree, which can be a
    static geometry, character mesh, UI element and so on.

    Each node has a transformation associated to it, which is local to the node.
    During rendering, that transformation will be chained to those of parent
    nodes and in turn, will affect children nodes.
    """

    def __init__(self):
        self._children = []
        self.parent = None
        self.transform = Mat()

    def render(self, ctx, transform):
        """Renders the node.

        This method should perform all rendering related calls, for which the
        passed computed transform should be used.

        :param ctx: Current render context.
        :type ctx: :class:`SceneRenderContext`

        :param transform: Node's computed transformation matrix. Not to be
            confused with `self.transform`, which describes node's local
            transformation.
        :type transform: :class:`matlib.Mat`
        """
        pass

    @property
    def children(self):
        """List tof children nodes."""
        return self._children

    def add_child(self, node):
        """Add a node as child.

        :param node: Node instance to add as child.
        :type node: a class derived from :class:`renderer.scene.SceneNode`

        :returns: The added node.
        :rtype: :class:`renderer.scene.SceneNode`
        """
        node.parent = self
        self._children.append(node)
        return node

    def remove_child(self, node):
        """Remove a child node.

        :param node: Node instance to remove.
        :type node: a class derived from :class:`renderer.scene.SceneNode`
        """
        try:
            self._children.remove(node)
            node.parent = None
        except ValueError:
            pass

    def to_world(self, pos):
        """Transform local coordinate to world.

        :param pos: Position in node's local coordinate system.
        :type pos: :class:`matlib.Vec`

        :returns: Position in world coordinates.
        :rtype: :class:`matlib.Vec`
        """
        transform = self.transform
        parent = self.parent
        while parent:
            transform *= transform
            parent = parent.parent

        return transform * pos


class RootNode(SceneNode):
    """A special node used as root for the scene tree, which `render()` method
    renders the entire tree and performs the parent-child transformations
    chaining.
    """

    def render(self, ctx, transform=None):
        self.t = Mat()

        def render_all(node, parent_transform):
            self.t.ident()
            self.t *= parent_transform
            self.t *= node.transform
            new_t = Mat() * self.t
            node.render(ctx, new_t)

            for child in node.children:
                render_all(child, new_t)

        for child in self.children:
            render_all(child, self.transform)


class MeshNode(SceneNode):
    """A node for attaching geometry (mesh) to the scene."""

    def __init__(self, mesh, props):
        """Constructor.

        :param mesh: Instance of the mesh to render.
        :type mesh: :class:`renderlib.mesh.Mesh`

        :param props: Instance of mesh rendering properties container.
        :tyep props: :class:`renderlib.core.MeshRenderProps`
        """
        super().__init__()
        self.mesh = mesh
        self.props = props

    def render(self, ctx, transform):
        self.props.model = transform
        self.props.view = ctx.modelview
        self.props.projection = ctx.projection
        render_mesh(self.mesh, self.props)


class TextNode(SceneNode):
    """A node for rendering text."""

    def __init__(self, text, props):
        """Constructor.

        :param text: Text renderable instance.
        :type text: :class:`renderlib.text.Text`

        :param props: Text rendering properties container.
        :type text: :class:`renderlib.core.TextRenderProps`
        """
        super().__init__()
        self.text = text
        self.props = props

    def render(self, ctx, transform):
        self.props.model = transform
        self.props.view = ctx.modelview
        self.props.projection = ctx.projection
        render_text(self.text, self.props)


class QuadNode(SceneNode):
    """A node for rendering 2D quads."""

    def __init__(self, size, props):
        """Constructor.

        :param size: Size of the quad.
        :type size: tuple or list

        :param props: Quad rendering properties container.
        :type props: :class:`renderlib.core.QuadRenderProps`
        """
        super().__init__()
        self._width, self._height = size
        self.props = props

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, w):
        self._width = w

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, h):
        self._height = h

    def render(self, ctx, transform):
        self.props.model = transform
        self.props.view = ctx.modelview
        self.props.projection = ctx.projection
        render_quad(self.width, self.height, self.props)


class LightNode(SceneNode):
    """Light source node."""

    def __init__(self, light):
        super().__init__()
        self.light = light

    def render(self, ctx, transform):
        aspect = ctx.renderer.width / ctx.renderer.height
        proj = Mat()
        proj.ortho(
            -5,
            +5,
            +5 * aspect,
            -5 * aspect,
            0,
            10)

        view = Mat()
        view.lookat(
            0, 5, 5,
            0, 0, 0,
            0, 1, 0)

        self.light.transform = proj * view * transform
