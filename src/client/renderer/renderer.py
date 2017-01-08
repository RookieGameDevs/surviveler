from exceptions import ConfigError
from renderlib.core import renderer_init
from renderlib.core import renderer_present
from renderlib.core import renderer_shutdown
from sdl2 import *
import logging


LOG = logging.getLogger(__name__)


class Renderer:
    """Renderer.

    This class provides methods for render system initialization, management and
    shutdown.
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
            gl_major, gl_minor = [
                int(v) for v in config.get('openglversion', '3.3').split('.')
            ]
        except (KeyError, TypeError, ValueError) as err:
            raise ConfigError(err)

        # create a SDL window
        self.win = SDL_CreateWindow(
            b'Surviveler',
            SDL_WINDOWPOS_CENTERED,
            SDL_WINDOWPOS_CENTERED,
            width,
            height,
            SDL_WINDOW_OPENGL)
        if self.win is None:
            raise RuntimeError('failed to create SDL window')

        # create an OpenGL context
        SDL_GL_SetAttribute(
            SDL_GL_CONTEXT_PROFILE_MASK,
            SDL_GL_CONTEXT_PROFILE_CORE)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, gl_major)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, gl_minor)
        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24)
        self.ctx = SDL_GL_CreateContext(self.win)

        if self.ctx is None:
            SDL_DestroyWindow(self.win)
            raise RuntimeError('failed to initialize OpenGL context')

        # initialize renderer
        renderer_init()

        self._width = width
        self._height = height

        LOG.info('renderer initialized; created {}x{} window'.format(
            width, height
        ))

    def __del__(self):
        self.shutdown()

    @property
    def width(self):
        """Render window width."""
        return self._width

    @property
    def height(self):
        """Render window height."""
        return self._height

    def clear(self):
        """Clear buffers."""
        # TODO

    def present(self):
        """Present updated buffers to screen."""
        renderer_present()
        SDL_GL_SwapWindow(self.win)

    def shutdown(self):
        """Shut down the renderer."""
        renderer_shutdown()
        SDL_GL_DeleteContext(self.ctx)
        self.ctx = None
        SDL_DestroyWindow(self.win)
        self.win = None
