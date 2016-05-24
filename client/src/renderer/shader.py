from OpenGL.GL import GL_ACTIVE_UNIFORMS
from OpenGL.GL import GL_ACTIVE_UNIFORM_BLOCKS
from OpenGL.GL import GL_COMPILE_STATUS
from OpenGL.GL import GL_DYNAMIC_DRAW
from OpenGL.GL import GL_FLOAT_MAT4
from OpenGL.GL import GL_FLOAT_VEC3
from OpenGL.GL import GL_FLOAT_VEC4
from OpenGL.GL import GL_INT
from OpenGL.GL import GL_LINK_STATUS
from OpenGL.GL import GL_SAMPLER_2D
from OpenGL.GL import GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS
from OpenGL.GL import GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES
from OpenGL.GL import GL_UNIFORM_BLOCK_BINDING
from OpenGL.GL import GL_UNIFORM_BLOCK_DATA_SIZE
from OpenGL.GL import GL_UNIFORM_BLOCK_NAME_LENGTH
from OpenGL.GL import GL_UNIFORM_BUFFER
from OpenGL.GL import GL_UNIFORM_OFFSET
from OpenGL.GL import glAttachShader
from OpenGL.GL import glBindBuffer
from OpenGL.GL import glBindBufferRange
from OpenGL.GL import glBufferData
from OpenGL.GL import glBufferSubData
from OpenGL.GL import glCompileShader
from OpenGL.GL import glCreateProgram
from OpenGL.GL import glCreateShader
from OpenGL.GL import glDeleteProgram
from OpenGL.GL import glGenBuffers
from OpenGL.GL import glGetActiveUniform
from OpenGL.GL import glGetActiveUniformBlockName
from OpenGL.GL import glGetActiveUniformBlockiv
from OpenGL.GL import glGetActiveUniformsiv
from OpenGL.GL import glGetProgramInfoLog
from OpenGL.GL import glGetProgramiv
from OpenGL.GL import glGetShaderInfoLog
from OpenGL.GL import glGetShaderiv
from OpenGL.GL import glGetUniformLocation
from OpenGL.GL import glLinkProgram
from OpenGL.GL import glShaderSource
from OpenGL.GL import glUniform1i
from OpenGL.GL import glUniform3fv
from OpenGL.GL import glUniform4fv
from OpenGL.GL import glUniformBlockBinding
from OpenGL.GL import glUniformMatrix4fv
from OpenGL.GL import glUseProgram
from exceptions import ShaderError
from functools import partial
from itertools import count
from matlib import Mat
from matlib import Vec
from renderer.texture import Texture
from utils import as_ascii
from utils import as_utf8
import ctypes


UNIFORM_TYPES_MAP = {
    GL_FLOAT_MAT4: Mat,
    GL_FLOAT_VEC3: Vec,
    GL_FLOAT_VEC4: Vec,
    GL_SAMPLER_2D: Texture,
    GL_INT: int,
}

UNIFORM_TYPES_SIZE_MAP = {
    GL_FLOAT_MAT4: ctypes.sizeof(ctypes.c_float) * 16,
    GL_FLOAT_VEC3: ctypes.sizeof(ctypes.c_float) * 3,
    GL_FLOAT_VEC4: ctypes.sizeof(ctypes.c_float) * 4,
    GL_SAMPLER_2D: ctypes.sizeof(ctypes.c_int),
    GL_INT: ctypes.sizeof(ctypes.c_int),
}


UNIFORM_CONVERTERS = {
    GL_FLOAT_MAT4: bytes,
    GL_FLOAT_VEC3: bytes,
    GL_FLOAT_VEC4: bytes,
    GL_SAMPLER_2D: lambda v: v.tex_unit,
    GL_INT: lambda v: v,
}


UNIFORM_DEFAULTS = {
    GL_FLOAT_MAT4: Mat,
    GL_FLOAT_VEC3: Vec,
    GL_FLOAT_VEC4: Vec,
    GL_SAMPLER_2D: lambda: Texture(0, 0, 0),
    GL_INT: lambda: 0,
}


UNIFORM_SETTERS = {
    GL_FLOAT_MAT4: lambda i, v: glUniformMatrix4fv(i, 1, True, v),
    GL_FLOAT_VEC3: lambda i, v: glUniform3fv(i, 1, v),
    GL_FLOAT_VEC4: lambda i, v: glUniform4fv(i, 1, v),
    GL_SAMPLER_2D: lambda i, v: glUniform1i(i, v),
    GL_INT: lambda i, v: glUniform1i(i, v),
}


class ShaderBlock:
    """Buffer-backed shader uniform block.

    NOTE: For internal use only."""

    def __init__(self, block_info):
        """Constructor; allocates an OpenGL buffer for the block and initializes
        it.

        :param block_info: Information about the uniform block.
        :type block_info: mapping
        """
        # create a new buffer big enough to contain all data for the shader
        # block
        self.buf = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buf)
        glBufferData(
            GL_UNIFORM_BUFFER,
            block_info['size'],
            ctypes.c_void_p(0),
            GL_DYNAMIC_DRAW)
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

        # initialize parameters
        self.params = {}
        for u_name, u_info in block_info['uniforms'].items():
            self.params[u_name] = {
                'type': u_info['type'],
                'value': None,
                'offset': u_info['offset'],
                'size': u_info['size'],
            }
            self[u_name] = UNIFORM_DEFAULTS[u_info['type']]()

        self.block_info = block_info

    def __getitem__(self, k):
        return self.params[k]['value']

    def __setitem__(self, k, v):
        param = self.params[k]
        if param['value'] != v:
            param['value'] = v
            glBindBuffer(GL_UNIFORM_BUFFER, self.buf)
            glBufferSubData(
                GL_UNIFORM_BUFFER,
                param['offset'],
                UNIFORM_TYPES_SIZE_MAP[param['type']],
                UNIFORM_CONVERTERS[param['type']](v))
            glBindBuffer(GL_UNIFORM_BUFFER, 0)

    def bind(self):
        glBindBufferRange(
            GL_UNIFORM_BUFFER,
            self.block_info['binding'],
            self.buf,
            0,
            self.block_info['size'])


class ShaderSource:
    def __init__(self, shader_type, shader_obj):
        """Constructor.

        TODO: add documentation
        """
        self.shader_type = shader_type
        self.shader_obj = shader_obj

    def __del__(self):
        """Destructor.

        Destroys the shader source object associated with instance.
        """
        # TODO: add implementation
        pass

    @classmethod
    def load_and_compile(cls, source, shader_type):
        shader_obj = glCreateShader(shader_type)
        glShaderSource(shader_obj, source)
        glCompileShader(shader_obj)
        if not glGetShaderiv(shader_obj, GL_COMPILE_STATUS):
            raise ShaderError('Failed to compile shader:\n{}'.format(
                as_utf8(glGetShaderInfoLog(shader_obj))))

        return cls(shader_type, shader_obj)


class Shader:
    """Shader program.

    A shader program performs the actual rendering of the geometry and defines
    its visual aspects: perspective transformation, color, shading, etc.

    This class abstracts the OpenGL shader program objects and provides a
    convenient interface for passing data to the pipeline.
    """

    def __init__(self, prog_id, params=None):
        """Constructor.

        :param prog_id: OpenGL program object identifier. Must identify a valid
            compiled and linked shader program.
        :type prog_id: int
        """
        self.prog = prog_id

        # create the uniforms map
        self.uniforms = {}
        for u_id in range(glGetProgramiv(self.prog, GL_ACTIVE_UNIFORMS)):
            u_name, u_size, u_type = glGetActiveUniform(self.prog, u_id)
            u_loc = glGetUniformLocation(self.prog, u_name)
            if u_loc >= 0:
                self.uniforms[as_ascii(u_name)] = {
                    'value': params.get(u_name, UNIFORM_DEFAULTS[u_type]()),
                    'loc': u_loc,
                    'type': u_type,
                    'size': u_size,
                }

        # create uniform blocks map
        self.uniform_blocks = {}
        binding_index = count()
        for ub_id in range(glGetProgramiv(self.prog, GL_ACTIVE_UNIFORM_BLOCKS)):
            # partial which retrieves a given parameter about uniform block
            binfo = partial(glGetActiveUniformBlockiv, self.prog, ub_id)

            # retrieve name
            name_len = binfo(GL_UNIFORM_BLOCK_NAME_LENGTH)
            name_buf = ctypes.create_string_buffer(int(name_len))
            glGetActiveUniformBlockName(self.prog, ub_id, name_len, None, name_buf)

            # retrieve number of active uniforms and pre-allocate arrays for
            # indices, sizes and offsets
            num_uniforms = int(binfo(GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS))
            uniform_indices = (ctypes.c_int * num_uniforms)()
            binfo(GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, uniform_indices)

            # offsets
            uniform_offsets = (ctypes.c_int * num_uniforms)()
            glGetActiveUniformsiv(
                self.prog,
                num_uniforms,
                uniform_indices,
                GL_UNIFORM_OFFSET,
                uniform_offsets)

            # assign a binding index to the uniform block
            glUniformBlockBinding(self.prog, ub_id, next(binding_index))

            # store info about the uniform block
            block = {
                'size': binfo(GL_UNIFORM_BLOCK_DATA_SIZE),
                'binding': binfo(GL_UNIFORM_BLOCK_BINDING),
                'uniforms': {
                    as_ascii(u_name).split('.', 1)[-1]: {
                        'type': u_type,
                        'size': u_size,
                        'offset': uniform_offsets[i],
                    } for i, (u_name, u_size, u_type) in enumerate([
                        glGetActiveUniform(self.prog, u_id)
                        for u_id in uniform_indices
                    ])
                },
            }
            self.uniform_blocks[as_ascii(name_buf.value)] = ShaderBlock(block)

    def __del__(self):
        """Destructor.

        Destroys the shader program object associated with instance.
        """
        glDeleteProgram(self.prog)

    @classmethod
    def from_glsl(cls, shaders, params=None):
        """Loads and compiles given shader files into a shader program.

        :param shaders: The shaders to be linked
        :type shaders: :class:`Shader`

        :returns: Linked shader.
        :rtype: :class:`renderer.Shader`

        :raises ShaderError: On I/O error, compile or linking failure or OpenGL
            error.
        """
        prog = glCreateProgram()
        for sh in shaders:
            glAttachShader(prog, sh.shader_obj)

        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            raise ShaderError('Failed to link shader program: {}'.format(
                glGetProgramInfoLog(prog)))

        return Shader(prog, params)

    def __getitem__(self, k):
        # check if there's a uniform with given name first
        uniform = self.uniforms.get(k)
        if uniform:
            return uniform['value']

        # attempt to lookup an uniform block
        try:
            block_name, param_name = k.split('.', 1)
            block = self.uniform_blocks.get(block_name)
            if block:
                return block[param_name]
        except (TypeError, KeyError, ValueError):
            raise ShaderError('Unknown shader parameter "{}"'.format(k))

    def __setitem__(self, k, v):
        # check if there's a uniform with given name first
        uniform = self.uniforms.get(k)
        if uniform:
            uniform['value'] = v
        else:
            try:
                block_name, param_name = k.split('.', 1)
                block = self.uniform_blocks.get(block_name)
                block[param_name] = v
            except (TypeError, KeyError, ValueError):
                import pdb; pdb.set_trace()
                raise ShaderError('Unknown shader parameter "{}"'.format(k))

    def use(self):
        """Makes the shader active and sets up its parameters (uniforms)."""
        glUseProgram(self.prog)

        # setup uniforms
        for uniform in self.uniforms.values():
            u_type = uniform['type']
            u_loc = uniform['loc']
            u_value = uniform['value']
            gl_value = UNIFORM_CONVERTERS[u_type](u_value)
            UNIFORM_SETTERS[u_type](u_loc, gl_value)

        # setup uniform blocks
        for block in self.uniform_blocks.values():
            block.bind()
