#include "ioutils.h"
#include "mesh.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define VERSION_MAJOR 1
#define VERSION_MINOR 0
#define MESH_VERSION (VERSION_MINOR << 4 | VERSION_MAJOR)

#define HEADER_SIZE 12

#define VERSION_FIELD uint8_t,  0
#define FORMAT_FIELD  uint16_t, 1
#define VCOUNT_FIELD  uint32_t, 3
#define ICOUNT_FIELD  uint32_t, 7
#define JCOUNT_FIELD  uint8_t,  11

#define invoke(macro, ...) macro(__VA_ARGS__)
#define cast(data, type, offset) (*(type*)(((char*)data) + offset))
#define get_field(data, field) invoke(cast, data, field)

enum {
	HAS_POSITION  = 1,
	HAS_NORMAL    = 1 << 1,
	HAS_UV        = 1 << 2,
	HAS_JOINTS    = 1 << 3
};

struct MeshData*
mesh_data_from_file(const char *filename)
{
	struct MeshData *md = NULL;

	// read file contents into a buffer
	char *data = NULL;
	size_t data_size = 0;
	if ((data_size = file_read(filename, &data)) == 0)
		return NULL;

	// check header and version
	if (data_size < HEADER_SIZE ||
	    get_field(data, VERSION_FIELD) != MESH_VERSION) {
		fprintf(stderr, "Invalid mesh header or unsupported version\n");
		goto error;
	}

	md = malloc(sizeof(struct MeshData));
	if (!md)
		goto error;
	memset(md, 0, sizeof(struct MeshData));

	// parse the header and check for vertices and indices
	md->vertex_format = get_field(data, FORMAT_FIELD);
	md->vertex_count = get_field(data, VCOUNT_FIELD);
	if (!(md->vertex_format & HAS_POSITION) || md->vertex_count == 0) {
		fprintf(stderr, "No vertex data provided\n");
		goto error;
	}

	md->index_count = get_field(data, ICOUNT_FIELD);
	if (md->index_count == 0) {
		fprintf(stderr, "No indices provided\n");
		goto error;
	}

	// compute vertex entry size based on the attributes specified in format
	// field
	md->vertex_size = 12;  // HAS_POSITION
	if (md->vertex_format & HAS_NORMAL)
		md->vertex_size += 12;
	if (md->vertex_format & HAS_UV)
		md->vertex_size += 8;
	if (md->vertex_format & HAS_JOINTS)
		md->vertex_size += 8;

	// initialize vertex data buffer
	size_t vdata_size = md->vertex_count * md->vertex_size;
	if (data_size < HEADER_SIZE + vdata_size) {
		fprintf(stderr, "Corrupted vertex data section\n");
		goto error;
	}
	if (!(md->vertex_data = malloc(vdata_size)))
		goto error;
	memcpy(md->vertex_data, data + HEADER_SIZE, vdata_size);

	// initialize index data buffer
	size_t idata_size = md->index_count * 4;
	if (data_size < HEADER_SIZE + vdata_size + idata_size) {
		fprintf(stderr, "Corrupted index data section\n");
		goto error;
	}
	if (!(md->index_data = malloc(idata_size)))
		goto error;
	memcpy(md->index_data, data + HEADER_SIZE + vdata_size, idata_size);

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
	glEnableVertexAttribArray(VERTEX_ATTRIB_POSITION);
	glVertexAttribPointer(
		VERTEX_ATTRIB_POSITION,
		3,
		GL_FLOAT,
		GL_FALSE,
		md->vertex_size,
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
			md->vertex_size,
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
