from OpenGL.GL import GL_R8
from OpenGL.GL import GL_RED
from OpenGL.GL import GL_TEXTURE0
from OpenGL.GL import GL_TEXTURE_2D
from OpenGL.GL import GL_UNSIGNED_BYTE
from OpenGL.GL import glActiveTexture
from OpenGL.GL import glBindTexture
from OpenGL.GL import glGenTextures
from OpenGL.GL import glTexStorage2D
from OpenGL.GL import glTexSubImage2D
from exceptions import SDLError
from renderer.texture import Texture
import ctypes
import sdl2 as sdl
import sdl2.sdlttf as ttf


TTF_INITIALIZED = False


class Font:
    """Font.

    This class incapsulates fonts loading and rendering primitives.
    """

    def __init__(self, filename, size):
        """Constructor.

        :param filename: Font file to load.
        :type filename: str

        :param size: Font size to use.
        :type size: int
        """
        global TTF_INITIALIZED
        if not TTF_INITIALIZED:
            ttf.TTF_Init()
            if not ttf.TTF_WasInit():
                raise SDLError('failed to initialize SDL font library: {}'.format(
                    ttf.TTF_GetError()))
            TTF_INITIALIZED = True

        self.font = ttf.TTF_OpenFont(filename.encode('utf8'), size)
        if not self.font:
            raise SDLError('failed to load font {} with size {}: {}'.format(
                filename,
                size,
                ttf.TTF_GetError()))

    def render_to_texture(self, text):
        """Renders the given string to a texture object.

        :param text: Text to render.
        :type text: str

        :returns: The resulting texture object.
        :rtype: :class:`renderer.Texture`
        """
        # render the text to a SDL_Surface structure
        surf_ptr = ttf.TTF_RenderText_Solid(
            self.font,
            text.encode('utf8'),
            sdl.SDL_Color())
        if not surf_ptr:
            raise SDLError('failed to render text to surface: {}'.format(
                ttf.TTF_GetError()))

        # retrieve a pointer to pixel data
        surf = surf_ptr.contents
        pixels = ctypes.cast(surf.pixels, ctypes.POINTER(ctypes.c_char))

        # create and fill an OpenGL rectangle texture (that is, a texture which
        # can have arbitrary non-power-of-two size and is accessed using
        # UV coordinates which are linearly mapped to the texture size)
        tex = glGenTextures(1)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_R8, surf.w, surf.h)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            surf.w,
            surf.h,
            GL_RED,
            GL_UNSIGNED_BYTE,
            pixels)
        glBindTexture(GL_TEXTURE_2D, 0)

        sdl.SDL_FreeSurface(surf_ptr)

        return Texture(tex, surf.w, surf.h, GL_TEXTURE_2D)
