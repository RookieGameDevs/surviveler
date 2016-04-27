from OpenGL.GL import GL_ACTIVE_UNIFORMS
from OpenGL.GL import GL_COMPILE_STATUS
from OpenGL.GL import GL_FLOAT_MAT4
from OpenGL.GL import GL_FRAGMENT_SHADER
from OpenGL.GL import GL_LINK_STATUS
from OpenGL.GL import GL_VERTEX_SHADER
from OpenGL.GL import glAttachShader
from OpenGL.GL import glCompileShader
from OpenGL.GL import glCreateProgram
from OpenGL.GL import glCreateShader
from OpenGL.GL import glGetActiveUniform
from OpenGL.GL import glGetProgramInfoLog
from OpenGL.GL import glGetProgramiv
from OpenGL.GL import glGetShaderInfoLog
from OpenGL.GL import glGetShaderiv
from OpenGL.GL import glLinkProgram
from OpenGL.GL import glShaderSource
from OpenGL.GL import glUniformMatrix4fv
from OpenGL.GL import glUseProgram
from exceptions import ShaderError
from exceptions import UniformError
from utils import as_ascii
from utils import as_utf8
import numpy as np


UNIFORM_VALIDATORS = {
    GL_FLOAT_MAT4: lambda v: (
        type(v) == np.ndarray and
        v.dtype == np.float32 and
        v.shape == (4, 4)),
}


UNIFORM_SETTERS = {
    GL_FLOAT_MAT4: lambda p, i, v: glUniformMatrix4fv(i, 1, True, v),
}


class Shader:
    """Shader program.

    A shader program performs the actual rendering of the geometry and defines
    its visual aspects: perspective transformation, color, shading, etc.

    This class abstracts the OpenGL shader program objects and provides a
    convenient interface for passing data to the pipeline.
    """

    def __init__(self, prog_id):
        """Constructor.

        :param prog_id: OpenGL program object identifier. Must identify a valid
            compiled and linked shader program.
        :type prog_id: int
        """
        self.prog = prog_id

        # create the uniforms map
        self.uniforms = {}
        for u_id in range(glGetProgramiv(self.prog, GL_ACTIVE_UNIFORMS)):
            name, size, prim_type = glGetActiveUniform(self.prog, u_id)
            self.uniforms[as_ascii(name)] = {
                'index': u_id,
                'type': prim_type,
                'size': size,
            }

    @classmethod
    def from_glsl(cls, vert_shader_file, frag_shader_file):
        """Loads and compiles given shader files into a shader program.

        :param vert_shader_file: File name of the vertex shader.
        :type vert_shader_file: str

        :param frag_shader_file: File name of the fragment shader.
        :type frag_shader_file: str

        :returns: Compiled and linked shader.
        :rtype: :class:`renderer.Shader`

        :raises ShaderError: On I/O error, compile or linking failure or OpenGL
            error.
        """

        def load_and_compile(filename, shader_type):
            try:
                with open(filename, 'r') as fp:
                    source = fp.read()
                    shader_obj = glCreateShader(shader_type)
                    glShaderSource(shader_obj, source)
                    glCompileShader(shader_obj)
                    if not glGetShaderiv(shader_obj, GL_COMPILE_STATUS):
                        raise ShaderError('Failed to compile shader "{}":\n{}'.format(
                            filename,
                            as_utf8(glGetShaderInfoLog(shader_obj))))

                    return shader_obj

            except IOError as err:
                raise ShaderError('Failed to load shader "{}": {}'.format(err))

        vert_shader = load_and_compile(vert_shader_file, GL_VERTEX_SHADER)
        frag_shader = load_and_compile(frag_shader_file, GL_FRAGMENT_SHADER)

        prog = glCreateProgram()
        glAttachShader(prog, vert_shader)
        glAttachShader(prog, frag_shader)
        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            raise ShaderError('Failed to link shader program: {}'.format(
                glGetProgramInfoLog(prog)))

        return Shader(prog)

    def use(self, params):
        """Makes the shader active and sets up its parameters (uniforms).

        :param params: Mapping of parameter names to their values.
        :type params: map

        :raises UniformError: On attempt to set an undefined uniform or pass
            data of wrong type.
        """
        glUseProgram(self.prog)

        # setup uniforms
        for k, v in params.items():
            try:
                uni_info = self.uniforms[k]
                if not UNIFORM_VALIDATORS[uni_info['type']](v):
                    raise UniformError('Invalid value for uniform "{}"'.format(k))
                UNIFORM_SETTERS[uni_info['type']](self.prog, uni_info['index'], v)
            except KeyError:
                raise UniformError('Uniform "{}" not found'.format(k))
