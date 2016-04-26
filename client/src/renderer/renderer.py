from OpenGL.GL import GL_COLOR_BUFFER_BIT
from OpenGL.GL import GL_SHADING_LANGUAGE_VERSION
from OpenGL.GL import GL_VERSION
from OpenGL.GL import glClear
from OpenGL.GL import glClearColor
from OpenGL.GL import glFlush
from OpenGL.GL import glGetString
from exceptions import ConfigError
from exceptions import OpenGLError
from exceptions import SDLError
from utils import as_utf8
import sdl2 as sdl


class Renderer:

    def __init__(self, config):
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

        print('OpenGL version: {}\nGLSL version: {}'.format(
            as_utf8(glGetString(GL_VERSION)),
            as_utf8(glGetString(GL_SHADING_LANGUAGE_VERSION))))

        self.gl_setup(width, height)

    def gl_setup(self, width, height):
        glClearColor(0, 0, 0, 0)

    def render(self, scene):
        glClear(GL_COLOR_BUFFER_BIT)

        scene.render(self)

        glFlush()
        sdl.SDL_GL_SwapWindow(self.window)

    def shutdown(self):
        sdl.SDL_GL_DeleteContext(self.gl_ctx)
        sdl.SDL_DestroyWindow(self.window)
