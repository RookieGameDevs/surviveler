from OpenGL.GL import GL_BACK
from OpenGL.GL import GL_BLEND
from OpenGL.GL import GL_COLOR_BUFFER_BIT
from OpenGL.GL import GL_CULL_FACE
from OpenGL.GL import GL_CW
from OpenGL.GL import GL_DEPTH_BUFFER_BIT
from OpenGL.GL import GL_DEPTH_TEST
from OpenGL.GL import GL_ONE_MINUS_SRC_ALPHA
from OpenGL.GL import GL_SHADING_LANGUAGE_VERSION
from OpenGL.GL import GL_SRC_ALPHA
from OpenGL.GL import GL_VERSION
from OpenGL.GL import glBlendFunc
from OpenGL.GL import glClear
from OpenGL.GL import glClearColor
from OpenGL.GL import glCullFace
from OpenGL.GL import glEnable
from OpenGL.GL import glFlush
from OpenGL.GL import glFrontFace
from OpenGL.GL import glGetString
from exceptions import ConfigError
from exceptions import OpenGLError
from exceptions import SDLError
from utils import as_utf8
import logging
import sdl2 as sdl


LOG = logging.getLogger(__name__)


class RenderOp:
    """Single render operation."""

    def __init__(self, shader, mesh, op):
        self.mesh = mesh
        self.shader = shader
        self.op = op

    def __call__(self):
        self.op()


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
            depth = int(config.get('depth', 24))
            gl_major, gl_minor = [
                int(v) for v in config.get('openglversion', '3.3').split('.')
            ]
        except (KeyError, TypeError, ValueError) as err:
            raise ConfigError(err)

        # window creation
        self.window = sdl.SDL_CreateWindow(
            b"Surviveler",
            sdl.SDL_WINDOWPOS_CENTERED,
            sdl.SDL_WINDOWPOS_CENTERED,
            width,
            height,
            sdl.SDL_WINDOW_OPENGL)
        if self.window is None:
            raise SDLError('Unable to create a {}x{}x{} window'.format(
                width, height, depth))

        # OpenGL 3.3 core profile context initialization
        sdl.SDL_GL_SetAttribute(
            sdl.SDL_GL_CONTEXT_PROFILE_MASK,
            sdl.SDL_GL_CONTEXT_PROFILE_CORE)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_CONTEXT_MAJOR_VERSION, gl_major)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_CONTEXT_MINOR_VERSION, gl_minor)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_DOUBLEBUFFER, 1)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_DEPTH_SIZE, depth)

        self.gl_ctx = sdl.SDL_GL_CreateContext(self.window)
        if self.gl_ctx is None:
            raise OpenGLError('Unable to create OpenGL {}.{} context'.format(
                gl_major, gl_minor))

        LOG.info('OpenGL version: {}'.format(as_utf8(glGetString(GL_VERSION))))
        LOG.info('GLSL version: {}'.format(
            as_utf8(glGetString(GL_SHADING_LANGUAGE_VERSION))))

        self._width = width
        self._height = height
        self.gl_setup(width, height)
        self.render_queue = []

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

        # flip the winding order
        glFrontFace(GL_CW)

        # enable depth buffer
        glEnable(GL_DEPTH_TEST)

        # enable alpha-blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # clear to black
        glClearColor(0, 0, 0, 0)

    def clear(self):
        """Clear buffers."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def add_render_op(self, op):
        """Add a rendering operation to render queue."""
        self.render_queue.append(op)

    def present(self):
        """Present updated buffers to screen."""

        def sort_key(op):
            return (op.shader.prog, op.mesh.vao)

        for op in sorted(self.render_queue, key=sort_key):
            op()

        glFlush()
        self.render_queue.clear()
        sdl.SDL_GL_SwapWindow(self.window)

    def shutdown(self):
        """Shuts down the renderer.

        Destroys the OpenGL context and the window associated with the renderer.
        """
        sdl.SDL_GL_DeleteContext(self.gl_ctx)
        sdl.SDL_DestroyWindow(self.window)
