from OpenGL.GL import GL_ARRAY_BUFFER
from OpenGL.GL import GL_ELEMENT_ARRAY_BUFFER
from OpenGL.GL import GL_FALSE
from OpenGL.GL import GL_FLOAT
from OpenGL.GL import GL_STATIC_DRAW
from OpenGL.GL import GL_TRIANGLES
from OpenGL.GL import GL_UNSIGNED_INT
from OpenGL.GL import glBindBuffer
from OpenGL.GL import glBindVertexArray
from OpenGL.GL import glBufferData
from OpenGL.GL import glDeleteBuffers
from OpenGL.GL import glDeleteVertexArrays
from OpenGL.GL import glDrawElements
from OpenGL.GL import glEnableVertexAttribArray
from OpenGL.GL import glGenBuffers
from OpenGL.GL import glGenVertexArrays
from OpenGL.GL import glVertexAttribPointer
import ctypes
import numpy as np


class Mesh:
    """Basic geometry unit which represents a solid model.

    This class is a convenient abstraction over OpenGL objects and provides a
    simple way to create and render geometry.

    NOTE: it should be instantiated and used only when a valid OpenGL 3.0+
    context is set up and active.
    """

    def __init__(self, vertices, indices, normals=None, uvs=None):
        """Constructor.

        Creates and initializes corresponding OpenGL objects with given data.

        :param vertices: Vertex data, specified as a contiguous list of X,Y,Z
            floating point values.
        :type vertices: list

        :param indices: Indices which identify model faces. The only supported
            geometry primitive is the triangle, thus, the size of indices list must
            be a multiple of 3.
        :type indices: list

        :param normals: Normals data, specified as a contiguos list of Xn,Yn,Zn
            floating point values. List length must be a multiple of 3.
        :type normals: list

        :param uvs: List of texture coordinates, specified as a contigous array
            of U,V floating pont values.. List length must be a multiple of 2.
        :type uvs: list
        """
        if len(vertices) < 3 or len(vertices) % 3:
            raise ValueError(
                'Vertex data must be an array of floats, which length is a '
                'positive multiple of 3')

        if len(indices) < 3 or len(indices) % 3:
            raise ValueError('Indices count must be a positive multiple of 3')

        if normals and (len(normals) < 3 or len(normals) % 3):
            raise ValueError(
                'Normals data must be an array of floats, which length is a '
                'positive multiple of 3')

        if uvs is not None and len(uvs) % 2:
            raise ValueError('UVs count must be a positive multiple of 2')

        self.num_elements = len(indices)

        # generate vertex array object and make it active
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # generate buffers
        self.buffers = glGenBuffers(2)
        vbo, ibo = self.buffers

        # initialize vertex buffer
        vertex_data = np.array(vertices, np.float32)

        # append normals data, if provided
        normals_offset = 0
        if normals:
            normals_offset = vertex_data.nbytes
            vertex_data = np.append(vertex_data, np.array(normals, np.float32))

        # append UVs data, if provided
        uvs_offset = 0
        if uvs:
            uvs_offset = vertex_data.nbytes
            vertex_data = np.append(vertex_data, np.array(uvs, np.float32))

        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

        # initialize index buffer
        index_data = np.array(indices, np.uint32)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL_STATIC_DRAW)

        # specify first attribute as vertex data
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # if provided, specify normals as second attribute
        if normals is not None:
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(
                1,
                3,
                GL_FLOAT,
                GL_FALSE,
                0,
                ctypes.c_void_p(normals_offset))

        # if provided, specify UVs as third attribute
        if uvs is not None:
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(
                2,
                2,
                GL_FLOAT,
                GL_FALSE,
                0,
                ctypes.c_void_p(uvs_offset))

        # unbind the vertex array object
        glBindVertexArray(0)

    def __del__(self):
        """Destructor.

        Destroys the VAO and related buffers associated with mesh.
        """
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(len(self.buffers), self.buffers)

    def render(self, rndr):
        """Draws the model using the given renderer.

        NOTE: The current OpenGL context is used, thus, there *MUST* be one set
        up and active before calling this method.

        :param rndr: Renderer to use.
        :type rndr: :class:`renderer.Renderer`
        """
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.num_elements, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)


class Rect(Mesh):
    """2D rectangle mesh with origin in top left corner."""

    def __init__(self, width, height, normalize_uvs=True):
        """Constructor.

        :param width: Width of the rectangle.
        :type width: float

        :param height: Height of the rectangle.
        :type height: float

        :param normalize_uvs: Should UV coordinates be in [0, 1] range or
            extend to width and height values.
        :type normalize_uvs: bool
        """
        left = 0
        top = height
        right = width
        bottom = 0
        vertices = [
            left, top, 0.0,
            left, bottom, 0.0,
            right, bottom, 0.0,
            right, top, 0.0,
        ]
        indices = [
            0, 1, 2,
            0, 2, 3,
        ]
        u = 1.0 if normalize_uvs else width
        v = 1.0 if normalize_uvs else height
        uvs = [
            0, 0,
            0, v,
            u, v,
            u, 0,
        ]
        super(Rect, self).__init__(vertices, indices, uvs=uvs)
