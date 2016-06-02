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
from OpenGL.GL import glDeleteProgram
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
from collections import defaultdict
from exceptions import ShaderError
from exceptions import UniformError
from matlib import Mat
from matlib import Vec
from renderer.texture import Texture
from utils import as_ascii
from utils import as_utf8


UNIFORM_TYPES_MAP = {
    GL_FLOAT_MAT4: Mat,
    GL_FLOAT_VEC3: Vec,
    GL_SAMPLER_2D: Texture,
    GL_INT: int,
}


def pass_through(v):
    return v


UNIFORM_CONVERTERS = {
    GL_FLOAT_MAT4: bytes,
    GL_FLOAT_VEC3: bytes,
    GL_SAMPLER_2D: lambda v: v.tex_unit,
    GL_INT: pass_through,
}


UNIFORM_DEFAULTS = {
    GL_FLOAT_MAT4: Mat,
    GL_FLOAT_VEC3: Vec,
    GL_SAMPLER_2D: lambda: Texture(0, 0, 0),
    GL_INT: lambda: 0,
}


UNIFORM_SETTERS = {
    GL_FLOAT_MAT4: lambda i, v: glUniformMatrix4fv(i, 1, True, v),
    GL_FLOAT_VEC3: lambda i, v: glUniform3fv(i, 1, v),
    GL_SAMPLER_2D: lambda i, v: glUniform1i(i, v),
    GL_INT: lambda i, v: glUniform1i(i, v),
}


ACTIVE_PROG = None
UNIFORMS_CACHE = defaultdict(dict)


class ShaderParam:
    """Shader parameter (uniform) proxy object.

    A shader parameter is a single value which can be passed to the shader
    during rendering.
    """

    def __init__(self, name, value, gl_type, gl_loc, gl_setter):
        """Constructor.

        :param name: Name of the parameter (uniform variable name).
        :type name: str

        :param value: Value to be passed to the uniform.
        :type value: any of supported types

        :param gl_type: OpenGL enum value of the uniform type.
        :type gl_type: int

        :param gl_loc: Location of the uniform in the shader program.
        :type gl_loc: int

        :param gl_setter: Uniform setter function.
        :type gl_setter: function
        """
        self.name = name
        self._value = None
        self.gl_value = None
        self.gl_loc = gl_loc
        self.gl_type = gl_type
        self.gl_setter = gl_setter
        self.value = value

    @property
    def value(self):
        """Current parameter value."""
        return self._value

    @value.setter
    def value(self, new_value):
        """Set the parameter value."""
        if self._value != new_value:
            self._value = new_value
            self.gl_value = UNIFORM_CONVERTERS[self.gl_type](new_value)

    def set(self):
        """Update the uniform with current parameter value."""
        self.gl_setter(self.gl_loc, self.gl_value)


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

    def __del__(self):
        """Destructor.

        Destroys the shader program object associated with instance.
        """
        glDeleteProgram(self.prog)

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

    def make_param(self, name, value=None):
        """Instantiates a shader parameter for the given shader.

        :param name: Name of the parameter (shader uniform variable name).
        :type name: str

        :param value: The initial value or `None`.
        :type value: any of supported types

        :returns: The created shader parameter.
        :rtype: :class:`renderer.shader.ShaderParam`

        :raises: :class`exceptions.UniformError` if no parameter with given name
            is defined in the shader program or a wrong value type is passed.
        """
        try:
            uni_info = self.uniforms[name]
        except KeyError:
            raise UniformError('Unknown uniform {}'.format(name))

        uni_type = uni_info['type']
        uni_loc = uni_info['loc']
        value = value or UNIFORM_DEFAULTS[uni_type]()

        exp_type = UNIFORM_TYPES_MAP[uni_type]
        if exp_type != type(value):
            raise UniformError('Uniform {} is of type {}, got {}'.format(
                name, exp_type, type(value)))

        return ShaderParam(
            name,
            value,
            uni_type,
            uni_loc,
            UNIFORM_SETTERS[uni_type])

    def use(self, params):
        """Makes the shader active and sets up its parameters (uniforms).

        :param params: List of parameters to use for the shader.
        :type params: list of :class:`renderer.shader.ShaderParam` items
        """
        global ACTIVE_PROG
        global UNIFORMS_CACHE
        cache = UNIFORMS_CACHE[ACTIVE_PROG]

        # in case the last used program is different from current one, make the
        # current one active and invalidate the cache
        if self.prog != ACTIVE_PROG:
            ACTIVE_PROG = self.prog
            glUseProgram(self.prog)
            cache.clear()

        # setup uniforms
        for p in params:
            # in case a value is cached and did not changed, skip the
            # submission to OpenGL
            cached_v = cache.get(p.name)
            if cached_v == p.gl_value:
                continue

            # update the cache and set the uniform
            cache[p.name] = p.gl_value
            p.set()
