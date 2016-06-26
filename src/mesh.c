#include "ioutils.h"
#include "mesh.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define unpack(data, t, off) (*(t*)(data + off))

enum {
	HAS_COORD  = 1,
	HAS_NORMAL = 1 << 1,
	HAS_UV     = 1 << 2,
	HAS_WEIGHT = 1 << 3
};

struct MeshData*
mesh_data_from_file(const char *filename)
{
	// read file contents into a buffer
	char *data = NULL;
	if (!file_read(filename, &data))
		return NULL;

	struct MeshData *md = malloc(sizeof(struct MeshData));
	if (!md)
		goto error;
	memset(md, 0, sizeof(struct MeshData));

	// parse the header
	//md->vertex_format = unpack(data, uint16_t, 0);
	md->vertex_format = HAS_COORD;
	md->vertex_count = unpack(data, uint32_t, 2);
	md->index_count = unpack(data, uint32_t, 6);
	md->vertex_size = 12;  // HAS_COORD

	/*
	if (md->vertex_format & HAS_NORMAL)
		md->vertex_size += 12;
	*/

	// initialize vertex data buffer
	size_t size = md->vertex_count * md->vertex_size;
	md->vertex_data = malloc(size);
	if (!md->vertex_data)
		goto error;
	memcpy(md->vertex_data, data + 11, size);

	// initialize index data buffer
	md->index_data = malloc(md->index_count * 4);
	if (!md->index_data)
		goto error;
	memcpy(md->index_data, data + 11 + size, md->index_count * 4);

cleanup:
	free(data);
	return md;

error:
	free(md);
	md = NULL;
	goto cleanup;
}

void
mesh_data_free(struct MeshData *md)
{
	if (md) {
		free(md->index_data);
		free(md->vertex_data);
		free(md);
	}
}

struct Mesh*
mesh_new(struct MeshData *md)
{
	GLenum gl_err = GL_NO_ERROR;
	char *errmsg = NULL;

	struct Mesh *m = malloc(sizeof(struct Mesh));
	if (!m)
		return NULL;
	memset(m, 0, sizeof(struct Mesh));

	// create VAO
	glGenVertexArrays(1, &m->vao);
	if (!m->vao || (gl_err = glGetError()) != GL_NO_ERROR) {
		errmsg = "VAO creation failed";
		goto error;
	}
	glBindVertexArray(m->vao);

	// allocate two GL buffers, one for vertex data, other for indices
	GLuint bufs[2];
	glGenBuffers(2, bufs);
	if (bufs[0] == 0 || bufs[1] == 0 ||
	    (gl_err = glGetError()) != GL_NO_ERROR) {
		errmsg = "VBO creation failed";
		goto error;
	}
	m->vbo = bufs[0];
	m->ibo = bufs[1];

	// initialize vertex data buffer
	glBindBuffer(GL_ARRAY_BUFFER, m->vbo);
	glBufferData(
		GL_ARRAY_BUFFER,
		md->vertex_count * md->vertex_size,
		md->vertex_data,
		GL_STATIC_DRAW
	);
	if ((gl_err = glGetError()) != GL_NO_ERROR) {
		errmsg = "VBO initialization failed";
		goto error;
	}

	// enable coord attribute
	glEnableVertexAttribArray(VERTEX_ATTRIB_COORD);
	glVertexAttribPointer(
		VERTEX_ATTRIB_COORD,
		3,
		GL_FLOAT,
		GL_FALSE,
		md->vertex_size - 12,
		(void*)(0)
	);

	// enable normal attribute
	if (md->vertex_format & HAS_NORMAL) {
		glEnableVertexAttribArray(VERTEX_ATTRIB_NORMAL);
		glVertexAttribPointer(
			VERTEX_ATTRIB_NORMAL,
			3,
			GL_FLOAT,
			GL_FALSE,
			md->vertex_size - 12,
			(void*)(12)
		);
	}

	// initialize index data buffer
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, m->ibo);
	glBufferData(
		GL_ELEMENT_ARRAY_BUFFER,
		md->index_count * 4,
		md->index_data,
		GL_STATIC_DRAW
	);

	m->index_count = md->index_count;

cleanup:
	// reset the context
	glBindVertexArray(0);
	return m;

error:
	mesh_free(m);
	m = NULL;
	fprintf(
		stderr,
		"Mesh creation failed: %s (OpenGL error %d)\n",
		errmsg,
		gl_err
	);
	goto cleanup;
}

void
mesh_free(struct Mesh *m)
{
	if (m) {
		glDeleteVertexArrays(1, &m->vao);
		glDeleteBuffers(1, &m->vbo);
		glDeleteBuffers(1, &m->ibo);
		free(m);
	}
}

int
mesh_render(struct Mesh *m)
{
	glBindVertexArray(m->vao);
	glDrawElements(
		GL_TRIANGLES,
		m->index_count,
		GL_UNSIGNED_INT,
		(void*)(0)
	);
	GLenum err = glGetError();
	if (err != GL_NO_ERROR) {
		fprintf(stderr, "Mesh rendering failed (OpenGL error %d)\n", err);
		return 0;
	}
	return 1;
}
