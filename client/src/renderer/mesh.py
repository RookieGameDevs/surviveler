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
from OpenGL.GL import glDrawElements
from OpenGL.GL import glEnableVertexAttribArray
from OpenGL.GL import glGenBuffers
from OpenGL.GL import glGenVertexArrays
from OpenGL.GL import glVertexAttribPointer
import numpy as np


class Mesh:

    def __init__(self, vertices, indices):
        if len(vertices) == 0:
            raise ValueError('No vertex data')
        elif len(indices) < 3 or len(indices) % 3:
            raise ValueError('Indices count must be a positive multiple of 3')

        self.num_elements = len(indices)

        # generate vertex array object and make it active
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # generate buffers
        self.buffers = glGenBuffers(2)
        vbo, ibo = self.buffers

        # initialize vertex buffer
        vertex_data = np.array(vertices, np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

        # initialize index buffer
        index_data = np.array(indices, np.uint32)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, index_data.nbytes, index_data, GL_STATIC_DRAW)

        # specify first attribute as vertex data
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # unbind the vertex array object
        glBindVertexArray(0)

    def render(self, rndr):
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.num_elements, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
