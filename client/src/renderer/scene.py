from OpenGL.GL import GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS as MAX_TEXTURES
from contextlib import ExitStack
from exceptions import OpenGLError
from matlib import Mat4
from matlib import Vec3
from renderer.mesh import Rect
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


class GeometryNode(SceneNode):
    """A node for attaching static geometry (mesh) to the scene."""

    def __init__(self, mesh, shader, params=None, textures=None):
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

        :param textures: Textures to apply to the mesh
        :type textures: list of :class:`renderer.Texture`
        """
        super(GeometryNode, self).__init__()
        self.mesh = mesh
        self.shader = shader
        self.params = params or {}
        self.textures = textures or []

    def render(self, ctx, transform):
        self.params['transform'] = ctx.camera.modelview * transform
        self.params['projection'] = ctx.camera.projection

        if len(self.textures) >= MAX_TEXTURES:
            raise OpenGLError(
                'Too much textures to render ({}), maximum is {}'.format(
                    len(self.textures), MAX_TEXTURES))

        with ExitStack() as stack:
            for tex_unit, tex in enumerate(self.textures):
                stack.enter_context(tex.use(tex_unit))

            self.shader.use(self.params)
            self.mesh.render(ctx.renderer)


class TextNode(SceneNode):
    """A node for rendering static text."""

    def __init__(self, font, shader, text, color=Vec3(1, 1, 1)):
        super(TextNode, self).__init__()
        self.font = font
        self._text = None
        self.text = text
        self.shader = shader
        self.color = color

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        if self._text != text:
            self._text = text
            self._texture = self.font.render_to_texture(text)
            self._rect = Rect(self._texture.width, self._texture.height, False)

    @property
    def width(self):
        return self._texture.width

    @property
    def height(self):
        return self._texture.height

    def render(self, ctx, transform):
        params = {
            'transform': ctx.camera.modelview * transform,
            'projection': ctx.camera.projection,
            'width': self._texture.width,
            'height': self._texture.height,
            'tex': self._texture,
            'color': self.color,
        }
        with self._texture.use(0):
            self.shader.use(params)
            self._rect.render(ctx.renderer)
