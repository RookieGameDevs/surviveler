from OpenGL.GL import GL_RGB
from OpenGL.GL import GL_RGB8
from OpenGL.GL import GL_TEXTURE0
from OpenGL.GL import GL_TEXTURE_2D
from OpenGL.GL import GL_UNSIGNED_BYTE
from OpenGL.GL import glActiveTexture
from OpenGL.GL import glBindTexture
from OpenGL.GL import glGenTextures
from OpenGL.GL import glTexStorage2D
from OpenGL.GL import glTexSubImage2D
from PIL import Image


class Texture:
    """Two-dimensional texture.

    This class abstracts OpenGL texture objects and their usage in a convenient
    interface.
    """
    def __init__(self, tex_id):
        self.tex_id = tex_id

    @classmethod
    def from_file(cls, filename):
        img = Image.open(filename)
        w, h = img.size

        tex = glGenTextures(1)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGB8, w, h)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, img.tobytes())

        return Texture(tex)
