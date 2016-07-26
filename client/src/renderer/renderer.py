import OpenGL  # noqa
OpenGL.ERROR_CHECKING = False  # noqa

from OpenGL.GL import GL_BACK
from OpenGL.GL import GL_BLEND
from OpenGL.GL import GL_COLOR_BUFFER_BIT
from OpenGL.GL import GL_CULL_FACE
from OpenGL.GL import GL_DEPTH_BUFFER_BIT
from OpenGL.GL import GL_DEPTH_TEST
from OpenGL.GL import GL_FILL
from OpenGL.GL import GL_FRONT_AND_BACK
from OpenGL.GL import GL_LINE
from OpenGL.GL import GL_ONE_MINUS_SRC_ALPHA
from OpenGL.GL import GL_POINT
from OpenGL.GL import GL_SRC_ALPHA
from OpenGL.GL import glBlendFunc
from OpenGL.GL import glClear
from OpenGL.GL import glClearColor
from OpenGL.GL import glCullFace
from OpenGL.GL import glEnable
from OpenGL.GL import glPolygonMode
from contextlib import ExitStack
from enum import IntEnum
from enum import unique
from exceptions import ConfigError
from renderer.texture import Texture
import logging
import surrender


LOG = logging.getLogger(__name__)


@unique
class PolygonMode(IntEnum):
    """Polygon rasterization mode."""

    #: Render only vertices as points.
    points = GL_POINT

    #: Render only edges as lines.
    lines = GL_LINE

    #: Render entire triangles filled.
    fill = GL_FILL


class RenderOp:
    """Single render operation.

    This class incapsulates the context of rendering a single mesh, with its
    shader and shader parameters, textures, etc.

    The renderer internally can reorder rendering operations for better
    efficiency and less OpenGL context switches.
    """

    def __init__(
            self, key, shader, shader_params, mesh, textures=None,
            polygon_mode=PolygonMode.fill):
        """Constructor.

        :param key: The key for indexing purpose
        :type key: :class:`float`

        :param shader: Shader to use for rendering.
        :type shader: :class:`surrender.Shader`

        :param shader_params: Shader parameters to submit to the shader.
        :type shader_params: mapping

        :param mesh: Mesh to render.
        :type mesh: :class:`renderer.mesh.Mesh`

        :param textures: List of textures to make active and use during
            rendering.
        :type textures: list of :class:`renderer.texture.Texture` or `None`

        :param polygon_mode: Polygon rasterization mode to use during rendering.
        :type polygon_mode: :enum:`renderer.renderer.PolygonMode`
        """
        self.key = key
        self.mesh = mesh
        self.shader = shader
        self.shader_params = shader_params
        self.textures = textures or []
        self.polygon_mode = polygon_mode


class Renderer:
    """An OpenGL rendering context.

    A renderer abstracts OS-specific details like window creation and OpenGL
    context set up.
    """

    def __init__(self, config):
        """Constructor.

        Instantiates a window and sets up an OpenGL context for it, which is
        immediately made active, using the given configuration data.

        :param config: Renderer-specific configuration.
        :type config: mapping-like interface.
        """
        try:
            width = int(config['width'])
            height = int(config['height'])
            # depth = int(config.get('depth', 24))
            gl_major, gl_minor = [
                int(v) for v in config.get('openglversion', '3.3').split('.')
            ]
        except (KeyError, TypeError, ValueError) as err:
            raise ConfigError(err)

        surrender.init(width, height)

        self._width = width
        self._height = height
        self.gl_setup(width, height)
        self.render_queue = []

    def __del__(self):
        self.shutdown()

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def gl_setup(self, width, height):
        """Private."""
        # cut out invisible faces
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        # enable depth buffer
        glEnable(GL_DEPTH_TEST)

        # enable alpha-blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # clear to black
        glClearColor(0.3, 0.3, 0.3, 1)

    def clear(self):
        """Clear buffers."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def add_render_op(self, op):
        """Add a rendering operation to rendering queue.

        :param op: Rendering operation to perform.
        :type op: :class:`renderer.renderer.RenderOp`
        """
        self.render_queue.append(op)

    def present(self):
        """Present updated buffers to screen."""

        def sort_key(op):
            return (op.key, op.shader.prog)

        polygon_mode = PolygonMode.fill

        current_shader = None
        for op in sorted(self.render_queue, key=sort_key, reverse=True):
            # perform actual rendering
            with ExitStack() as stack:
                for tex_unit, tex in enumerate(op.textures):
                    stack.enter_context(tex.use(tex_unit))

                if op.shader.prog != current_shader:
                    op.shader.use()
                    current_shader = op.shader.prog

                for k, v in op.shader_params.items():
                    # FIXME: rework this
                    if isinstance(v, Texture):
                        v = v.tex_unit
                    op.shader[k] = v

                # change the polygon mode, if requested by render op
                if polygon_mode != op.polygon_mode:
                    glPolygonMode(GL_FRONT_AND_BACK, op.polygon_mode)
                    polygon_mode = op.polygon_mode

                op.mesh.render()

        self.render_queue.clear()

        surrender.render()

    def shutdown(self):
        """Shuts down the renderer.

        Destroys the OpenGL context and the window associated with the renderer.
        """
        surrender.shutdown()
