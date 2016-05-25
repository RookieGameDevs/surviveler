from OpenGL.GL import GL_CLAMP_TO_EDGE
from OpenGL.GL import GL_MIRRORED_REPEAT
from OpenGL.GL import GL_REPEAT
from OpenGL.GL import GL_RGB
from OpenGL.GL import GL_RGB8
from OpenGL.GL import GL_TEXTURE0
from OpenGL.GL import GL_TEXTURE_2D
from OpenGL.GL import GL_TEXTURE_WRAP_S
from OpenGL.GL import GL_TEXTURE_WRAP_T
from OpenGL.GL import GL_UNSIGNED_BYTE
from OpenGL.GL import glActiveTexture
from OpenGL.GL import glBindSampler
from OpenGL.GL import glBindTexture
from OpenGL.GL import glDeleteSamplers
from OpenGL.GL import glDeleteTextures
from OpenGL.GL import glGenSamplers
from OpenGL.GL import glGenTextures
from OpenGL.GL import glSamplerParameteri
from OpenGL.GL import glTexStorage2D
from OpenGL.GL import glTexSubImage2D
from PIL import Image
from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from enum import IntEnum
from enum import unique


class TextureParam(ABC):

    @abstractmethod
    def apply(self, sampler):
        """Applies a texture parameter to given sampler.

        :param sampler: The OpenGL identifier for the sampler object.
        :type sampler: int
        """


class TextureParamWrap(TextureParam):

    @unique
    class Coord(IntEnum):
        t = GL_TEXTURE_WRAP_T
        s = GL_TEXTURE_WRAP_S

    @unique
    class WrapType(IntEnum):
        repeat = GL_REPEAT
        repeat_mirrored = GL_MIRRORED_REPEAT
        clamp = GL_CLAMP_TO_EDGE

    def __init__(self, coord, wrap_type):
        """Constructor.

        :param coord: Coordinate along which to wrap.
        :type coord: :class:`renderer.TextureParamWrap.Coord`

        :param wrap_type: Type of wrap to perform.
        :type wrap_type: :enum:`renderer.TextureParamWrap.WrapType`
        """
        self.coord = coord
        self.wrap_type = wrap_type

    def apply(self, sampler):
        glSamplerParameteri(sampler, self.coord, self.wrap_type)


class Texture:
    """Two-dimensional texture.

    This class abstracts OpenGL texture objects and their usage in a convenient
    interface.
    """
    def __init__(self, tex_id, width, height, tex_type=GL_TEXTURE_2D):
        """Constructor.

        :param tex_id: Identifier of OpenGL object representing the texture.
        :type tex_id: int

        :param width: Width of the texture.
        :type width: int

        :param height: Height of the texture.
        :type height: int

        :param tex_type: OpenGL type of the texture. Must be a valid 2D texture
            enum value.
        :type tex_type: int
        """
        self.tex_id = tex_id
        self.tex_type = tex_type
        self.tex_unit = 0
        self.sampler = glGenSamplers(1)
        self._width = width
        self._height = height

    def __del__(self):
        """Destructor.

        Destroys texture and sampler objects associated with the instance.
        """
        glDeleteTextures(self.tex_id)
        glDeleteSamplers(1, [self.sampler])
        self.tex_id = self.sampler = 0

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def set_param(self, param):
        """Applies sampling parameter.

        :param param: Parameter to apply.
        :type param: subclass of :class:`renderer.TextureParam`
        """
        param.apply(self.sampler)

    @classmethod
    def from_image(cls, image):
        """Creates a texture from given image file.

        :param image: Image.
        :type image: :class:`PIL.Image`

        :returns: The texture instance.
        :rtype: :class:`renderer.Texture`
        """
        w, h = image.size

        tex = glGenTextures(1)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGB8, w, h)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE, image.tobytes())
        glBindTexture(GL_TEXTURE_2D, 0)

        return Texture(tex, w, h)

    @contextmanager
    def use(self, tex_unit):
        """Makes the given texture as active in the rendering pipeline.

        :param tex_unit: OpenGL texture image unit to make active.
        :type tex_unit: int
        """
        self.tex_unit = tex_unit
        glActiveTexture(GL_TEXTURE0 + self.tex_unit)
        glBindTexture(self.tex_type, self.tex_id)
        glBindSampler(self.tex_unit, self.sampler)
        yield
        glBindTexture(self.tex_type, 0)
