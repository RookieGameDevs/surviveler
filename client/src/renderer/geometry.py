from renderer.renderer import RenderOp
from renderer.scene import SceneNode


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
        self.params['transform'] = transform
        self.params['modelview'] = ctx.modelview
        self.params['projection'] = ctx.projection

        # schedule the node rendering
        ctx.renderer.add_render_op(RenderOp(
            self.shader,
            self.params,
            self.mesh,
            self.textures))
