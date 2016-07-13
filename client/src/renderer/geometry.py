from itertools import chain
from renderer.light import LIGHT_SOURCES
from renderer.renderer import RenderOp
from renderer.scene import SceneNode
from matlib import Vec


class GeometryNode(SceneNode):
    """A node for attaching static geometry (mesh) to the scene."""

    def __init__(
            self, mesh, shader, params=None, textures=None, enable_light=False,
            animation=None):
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

        :param enable_light: Enable lighting for the node.
        :type enable_light: bool
        """
        super().__init__()
        self.mesh = mesh
        self.shader = shader
        self.params = params or {}
        self.textures = textures or []
        self.enable_light = enable_light
        self.anim_inst = animation
        self._animate = False

    @property
    def animate(self):
        return self._animate

    @animate.setter
    def animate(self, value):
        self._animate = value

    def render(self, ctx, transform):
        self.params['transform'] = transform
        self.params['modelview'] = ctx.modelview
        self.params['projection'] = ctx.projection

        if self.enable_light:
            self.params.update({
                'Light[{}].{}'.format(light_id, p): v for light_id, p, v in
                chain.from_iterable([
                    [(light_id, p, v) for p, v in params.items()] for light_id, params in
                    LIGHT_SOURCES.items()
                ])
            })

        if self.animate and self.anim_inst:
            self.params['animate'] = 1
            self.params['joints[0]'] = self.anim_inst.skin_transforms

        # compute absolute Z value of the node center for proper rendering order
        v = (ctx.view * transform) * Vec(0, 0, 0, 1)

        # schedule the node rendering
        ctx.renderer.add_render_op(RenderOp(
            v.z,
            self.shader,
            self.params,
            self.mesh,
            self.textures))
