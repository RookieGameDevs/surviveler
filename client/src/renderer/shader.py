from OpenGL.GL import GL_ACTIVE_UNIFORMS
from OpenGL.GL import GL_COMPILE_STATUS
from OpenGL.GL import GL_FLOAT_MAT4
from OpenGL.GL import GL_FLOAT_VEC3
from OpenGL.GL import GL_FRAGMENT_SHADER
from OpenGL.GL import GL_INT
from OpenGL.GL import GL_LINK_STATUS
from OpenGL.GL import GL_SAMPLER_2D
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
from OpenGL.GL import glGetUniformLocation
from OpenGL.GL import glLinkProgram
from OpenGL.GL import glShaderSource
from OpenGL.GL import glUniform1i
from OpenGL.GL import glUniform3fv
from OpenGL.GL import glUniformMatrix4fv
from OpenGL.GL import glUseProgram
from exceptions import ShaderError
from exceptions import UniformError
from matlib import Mat4
from matlib import Vec3
from renderer.texture import Texture
from utils import as_ascii
from utils import as_utf8
import numpy as np


UNIFORM_VALIDATORS = {
    GL_FLOAT_MAT4: lambda v: type(v) == Mat4,
    GL_FLOAT_VEC3: lambda v: type(v) == Vec3,
    GL_SAMPLER_2D: lambda v: type(v) == Texture,
    GL_INT: lambda v: type(v) == int,
}


UNIFORM_SETTERS = {
    GL_FLOAT_MAT4: lambda i, v: glUniformMatrix4fv(i, 1, True, np.asarray(v)),
    GL_FLOAT_VEC3: lambda i, v: glUniform3fv(i, 1, np.asarray(v)),
    GL_SAMPLER_2D: lambda i, v: glUniform1i(i, v.tex_unit),
    GL_INT: lambda i, v: glUniform1i(i, v),
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
                'loc': glGetUniformLocation(self.prog, name),
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
                # lookup uniform information
                uni_info = self.uniforms[k]

                # validate types
                if not UNIFORM_VALIDATORS[uni_info['type']](v):
                    raise UniformError('Invalid value for uniform "{}"'.format(k))

                # invoke the setter with uniform's location and new value as
                # arguments
                UNIFORM_SETTERS[uni_info['type']](uni_info['loc'], v)

            except KeyError:
                raise UniformError('Uniform "{}" not found'.format(k))
