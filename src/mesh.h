#pragma once

#include "anim.h"
#include "matlib.h"
#include <GL/glew.h>
#include <stddef.h>

enum VertexAttrib {
	VERTEX_ATTRIB_POSITION,
	VERTEX_ATTRIB_NORMAL,
	VERTEX_ATTRIB_UV,
	VERTEX_ATTRIB_JOINT_IDS,
	VERTEX_ATTRIB_JOINT_WEIGHTS
};

struct MeshData {
	int vertex_format;
	size_t vertex_size;
	size_t vertex_count;
	void *vertex_data;
	size_t index_count;
	uint32_t *index_data;
	struct Skeleton *skeleton;
	size_t anim_count;
	struct Animation *animations;
	Mat transform;
};


struct Mesh {
	GLuint vao;
	GLuint vbo;
	GLuint ibo;
	GLuint index_count;
};

struct MeshData*
mesh_data_from_file(const char *filename);

void
mesh_data_free(struct MeshData *md);

struct Mesh*
mesh_new(struct MeshData *md);

void
mesh_free(struct Mesh *m);

int
mesh_attrib_index(struct Mesh *m, enum VertexAttrib a);

int
mesh_render(struct Mesh *m);
