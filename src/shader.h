#pragma once

#include "matlib.h"
#include <GL/glew.h>
#include <stddef.h>

struct ShaderParam {
	const char *name;
	GLenum type;
	GLint loc;
	GLuint size;
};

struct Shader {
	GLuint prog;
	GLuint param_count;
	struct ShaderParam *params;
};

struct Shader*
shader_new(const char *vert_src, const char *frag_src);

void
shader_free(struct Shader *s);

struct Shader*
shader_load_and_compile(const char *vert_shader, const char *frag_shader);

int
shader_use(struct Shader *s);

const struct ShaderParam*
shader_get_param(struct Shader *s, const char *name);

int
shader_set_param_mat(const struct ShaderParam *p, size_t count, Mat *m);

int
shader_set_param_vec(const struct ShaderParam *p, size_t count, Vec *v);

int
shader_set_param_int(const struct ShaderParam *p, size_t count, int *i);

int
shader_set_param_float(const struct ShaderParam *p, size_t count, float *f);
