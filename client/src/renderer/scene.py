from matlib import Mat4
from matlib import Vec3
import numpy as np


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
        self.transform = Mat4()

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
        :type pos: :class:`matlib.Vec3`

        :returns: Position in world coordinates.
        :rtype: :class:`matlib.Vec3`
        """
        transform = self.transform
        parent = self.parent
        while parent:
            transform = parent.transform * transform
            parent = parent.parent

        v = transform * np.array([pos.x, pos.y, pos.z, 1.0]).reshape((4, 1))
        return Vec3(v[0], v[1], v[2])


class RootNode(SceneNode):
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
