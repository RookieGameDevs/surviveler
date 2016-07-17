// use open source standard library features
#define _XOPEN_SOURCE 700

#include "error.h"
#include "ioutils.h"
#include "mesh.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define VERSION_MAJOR 1
#define VERSION_MINOR 0
#define MESH_VERSION (VERSION_MINOR << 4 | VERSION_MAJOR)

#define HEADER_SIZE 78
#define POSITION_ATTRIB_SIZE 12
#define NORMAL_ATTRIB_SIZE 12
#define UV_ATTRIB_SIZE 8
#define JOINT_ATTRIB_SIZE 8
#define INDEX_SIZE 4
#define JOINT_SIZE 66
#define ANIM_SIZE  12
#define POSE_SIZE  41

#define VERSION_FIELD   uint8_t,  0
#define FORMAT_FIELD    uint16_t, 1
#define VCOUNT_FIELD    uint32_t, 3
#define ICOUNT_FIELD    uint32_t, 7
#define JCOUNT_FIELD    uint8_t,  11
#define ACOUNT_FIELD    uint16_t, 12
#define TRANSFORM_FIELD Mat,      14

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
	// read file contents into a buffer
	char *data = NULL;
	size_t data_size = 0;
	if ((data_size = file_read(filename, &data)) == 0)
		return NULL;

	// load mesh data
	struct MeshData *md = mesh_data_from_buffer(data, data_size);

	// cleanup
	free(data);

	return md;
}


struct MeshData*
mesh_data_from_buffer(const char *data, size_t data_size)
{
	struct MeshData *md = NULL;

	// check header and version
	if (data_size < HEADER_SIZE ||
	    get_field(data, VERSION_FIELD) != MESH_VERSION) {
		err("invalid mesh header or unsupported version");
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
		err("no vertex data provided");
		goto error;
	}

	md->index_count = get_field(data, ICOUNT_FIELD);
	if (md->index_count == 0) {
		err("no indices provided");
		goto error;
	}

	// parse root transformation
	md->transform = get_field(data, TRANSFORM_FIELD);

	// compute vertex entry size based on the attributes specified in format
	// field
	md->vertex_size = POSITION_ATTRIB_SIZE;  // HAS_POSITION
	if (md->vertex_format & HAS_NORMAL)
		md->vertex_size += NORMAL_ATTRIB_SIZE;
	if (md->vertex_format & HAS_UV)
		md->vertex_size += UV_ATTRIB_SIZE;
	if (md->vertex_format & HAS_JOINTS)
		md->vertex_size += JOINT_ATTRIB_SIZE;

	size_t offset = HEADER_SIZE;

	// initialize vertex data buffer
	size_t vdata_size = md->vertex_count * md->vertex_size;
	if (data_size < offset + vdata_size) {
		err("corrupted vertex data section");
		goto error;
	}
	if (!(md->vertex_data = malloc(vdata_size)))
		goto error;
	memcpy(md->vertex_data, data + offset, vdata_size);
	offset += vdata_size;

	// initialize index data buffer
	size_t idata_size = md->index_count * INDEX_SIZE;
	if (data_size < offset + idata_size) {
		err("corrupted index data section");
		goto error;
	}
	if (!(md->index_data = malloc(idata_size)))
		goto error;
	memcpy(md->index_data, data + offset, idata_size);
	offset += idata_size;

	// build the skeleton
	if (md->vertex_format & HAS_JOINTS) {
		size_t joint_count = get_field(data, JCOUNT_FIELD);
		size_t jdata_size = joint_count * JOINT_SIZE;
		if (data_size < offset + jdata_size) {
			err("corrupted joint data section");
			goto error;
		}

		if (!(md->skeleton = malloc(sizeof(struct Skeleton))))
			goto error;
		if (!(md->skeleton->joints = malloc(sizeof(struct Joint) * joint_count)))
			goto error;

		md->skeleton->joint_count = joint_count;
		for (size_t j = 0; j < joint_count; j++) {
			uint8_t id = *(uint8_t*)(data + offset);
			assert(id < joint_count);

			md->skeleton->joints[id].parent = *(uint8_t*)(data + offset + 1);
			md->skeleton->joints[id].inv_bind_pose = *(Mat*)(data + offset + 2);
			offset += JOINT_SIZE;
		}
	}

	// initialize animations (if there's a skeleton)
	md->anim_count = get_field(data, ACOUNT_FIELD);
	if (md->skeleton && md->anim_count > 0) {
		md->animations = malloc(sizeof(struct Animation) * md->anim_count);

		for (size_t a = 0; a < md->anim_count; a++) {
			struct Animation *anim = &md->animations[a];
			anim->skeleton = md->skeleton;
			anim->duration = *(float*)(data + offset);
			anim->speed = *(float*)(data + offset + 4);
			anim->pose_count = *(uint32_t*)(data + offset + 8);

			offset += ANIM_SIZE;

			// read timestamps
			anim->timestamps = malloc(sizeof(float) * anim->pose_count);
			if (!anim->timestamps)
				goto error; // TODO: free timestamp data
			for (size_t t = 0; t < anim->pose_count; t++) {
				anim->timestamps[t] = *(float*)(data + offset);
				offset += 4;
			}

			// read skeleton poses
			anim->poses = malloc(sizeof(struct SkeletonPose) * anim->pose_count);
			if (!anim->poses)
				goto error;  // TODO: free animation data
			for (size_t p = 0; p < anim->pose_count; p++) {
				struct SkeletonPose *sp = anim->poses + p;
				sp->skeleton = md->skeleton;

				sp->joint_poses = malloc(sizeof(struct JointPose) * md->skeleton->joint_count);
				if (!sp->skeleton || !sp->joint_poses)
					goto error;  // TODO: free skeleton pose data

				// read joint poses for given timestamp
				for (size_t j = 0; j < md->skeleton->joint_count; j++) {
					uint8_t id = *(uint8_t*)(data + offset);
					assert(id < md->skeleton->joint_count);

					struct JointPose *jp = &sp->joint_poses[id];

					// translation
					float tx = *(float*)(data + offset + 1);
					float ty = *(float*)(data + offset + 5);
					float tz = *(float*)(data + offset + 9);
					jp->trans = vec(tx, ty, tz, 0);

					// rotation
					float rw = *(float*)(data + offset + 13);
					float rx = *(float*)(data + offset + 17);
					float ry = *(float*)(data + offset + 21);
					float rz = *(float*)(data + offset + 25);
					jp->rot = qtr(rw, rx, ry, rz);

					// scale
					float sx = *(float*)(data + offset + 29);
					float sy = *(float*)(data + offset + 33);
					float sz = *(float*)(data + offset + 37);
					jp->scale = vec(sx, sy, sz, 0);

					offset += POSE_SIZE;
				}
			}
		}
	}

cleanup:
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
		if (md->skeleton)
			free(md->skeleton->joints);
		free(md->skeleton);
		free(md->animations);
		free(md);
	}
}

struct Mesh*
mesh_new(struct MeshData *md)
{
	GLenum gl_err = GL_NO_ERROR;

	struct Mesh *m = malloc(sizeof(struct Mesh));
	if (!m)
		return NULL;
	memset(m, 0, sizeof(struct Mesh));

	// create VAO
	glGenVertexArrays(1, &m->vao);
	if (!m->vao || (gl_err = glGetError()) != GL_NO_ERROR) {
		errf("VAO creation failed (OpenGL error %d)", gl_err);
		goto error;
	}
	glBindVertexArray(m->vao);

	// allocate two GL buffers, one for vertex data, other for indices
	GLuint bufs[2];
	glGenBuffers(2, bufs);
	if (bufs[0] == 0 || bufs[1] == 0 ||
	    (gl_err = glGetError()) != GL_NO_ERROR) {
		errf("VBO creation failed (OpenGL error %d)", gl_err);
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
		errf("VBO initialization failed (OpenGL error %d)", gl_err);
		goto error;
	}

	// enable coord attribute
	glEnableVertexAttribArray(VERTEX_ATTRIB_POSITION);
	size_t offset = 0;
	glVertexAttribPointer(
		VERTEX_ATTRIB_POSITION,
		3,
		GL_FLOAT,
		GL_FALSE,
		md->vertex_size,
		(void*)(offset)
	);
	offset += 12;

	// enable normal attribute
	if (md->vertex_format & HAS_NORMAL) {
		glEnableVertexAttribArray(VERTEX_ATTRIB_NORMAL);
		glVertexAttribPointer(
			VERTEX_ATTRIB_NORMAL,
			3,
			GL_FLOAT,
			GL_FALSE,
			md->vertex_size,
			(void*)(offset)
		);
		offset += 12;
	}

	// enable UV attribute
	if (md->vertex_format & HAS_UV) {
		glEnableVertexAttribArray(VERTEX_ATTRIB_UV);
		glVertexAttribPointer(
			VERTEX_ATTRIB_UV,
			2,
			GL_FLOAT,
			GL_FALSE,
			md->vertex_size,
			(void*)(offset)
		);
		offset += 8;
	}

	// initialize joint ID and weight attributes
	if (md->vertex_format & HAS_JOINTS) {
		glEnableVertexAttribArray(VERTEX_ATTRIB_JOINT_IDS);
		glVertexAttribIPointer(
			VERTEX_ATTRIB_JOINT_IDS,
			4,
			GL_UNSIGNED_BYTE,
			md->vertex_size,
			(void*)(offset)
		);
		offset += 4;

		glEnableVertexAttribArray(VERTEX_ATTRIB_JOINT_WEIGHTS);
		glVertexAttribPointer(
			VERTEX_ATTRIB_JOINT_WEIGHTS,
			4,
			GL_UNSIGNED_BYTE,
			GL_TRUE,
			md->vertex_size,
			(void*)(offset)
		);
		offset += 4;
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
	GLenum gl_err = glGetError();
	if (gl_err != GL_NO_ERROR) {
		errf("mesh rendering failed (OpenGL error %d)", gl_err);
		return 0;
	}
	return 1;
}
