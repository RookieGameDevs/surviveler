from OpenGL.GL import GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS as MAX_TEXTURES
from contextlib import ExitStack
from exceptions import OpenGLError
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
        self.params = {
            k: shader.make_param(k) for k in
            ('transform', 'modelview', 'projection')
        }
        self.textures = textures or []

    def render(self, ctx, transform):
        self.params['transform'].value = transform
        self.params['modelview'].value = ctx.modelview
        self.params['projection'].value = ctx.projection

        if len(self.textures) >= MAX_TEXTURES:
            raise OpenGLError(
                'Too much textures to render ({}), maximum is {}'.format(
                    len(self.textures), MAX_TEXTURES))

        with ExitStack() as stack:
            for tex_unit, tex in enumerate(self.textures):
                stack.enter_context(tex.use(tex_unit))

            self.shader.use(self.params.values())
            self.mesh.render(ctx.renderer)
