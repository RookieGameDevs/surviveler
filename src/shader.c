#include "error.h"
#include "ioutils.h"
#include "shader.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>

GLuint
shader_compile_source(const char *source, GLenum type)
{
	GLenum gl_err = GL_NO_ERROR;

	// create the shader
	GLuint shader = glCreateShader(type);
	if (!shader) {
		errf("failed to create shader (OpenGL error %d)", gl_err);
		goto error;
	}

	// set shader and compile it
	glShaderSource(shader, 1, (const char**)&source, NULL);
	glCompileShader(shader);

	int status = GL_FALSE;
	glGetShaderiv(shader, GL_COMPILE_STATUS, &status);
	if (status == GL_FALSE) {
		// fetch compile log
		int log_len;
		glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &log_len);
		char log[log_len];
		glGetShaderInfoLog(shader, log_len, NULL, log);

		errf("shader compile error: %s", log);
		goto error;
	}

	return shader;

error:
	shader_free_source(shader);
	return 0;
}

GLuint
shader_compile_file(const char *filename)
{
	const char *ext = strrchr(filename, '.');
	GLenum type;
	if (strncmp(ext, ".vert", 4) == 0) {
		type = GL_VERTEX_SHADER;
	} else if (strncmp(ext, ".frag", 4) == 0) {
		type = GL_FRAGMENT_SHADER;
	} else {
		errf(
			"bad shader source filename '%s'; "
			"extension must be .vert or .frag",
			filename
		);
		return 0;
	}

	char *source = NULL;
	if (!file_read(filename, &source))
		return 0;

	GLuint shader = shader_compile_source(source, type);
	if (!shader)
		errf("shader source '%s' compilation failed", filename);

	free(source);

	return shader;
}

void
shader_free_source(GLuint src)
{
	if (src)
		glDeleteShader(src);
}

static int
init_shader_params(struct Shader *s)
{
	// query the number of uniforms in shader proram
	GLuint count = 0;
	glGetProgramiv(s->prog, GL_ACTIVE_UNIFORMS, (GLint*)&count);
	if (count == 0) {
		s->param_count = 0;
		s->params = NULL;
		return 1;
	}

	// prepare name string buffer
	GLsizei name_len;
	glGetProgramiv(s->prog, GL_ACTIVE_UNIFORM_MAX_LENGTH, (GLint*)&name_len);
	GLchar name[name_len];

	s->param_count = count;
	s->params = malloc(count * sizeof(struct ShaderParam));
	if (!s->params)
		goto error;
	memset(s->params, 0, count * sizeof(struct ShaderParam));

	// query information about each uniform
	for (GLuint u = 0; u < count; u++) {
		GLsizei actual_len = 0;
		struct ShaderParam *sp = s->params + u;
		glGetActiveUniform(
			s->prog,
			u,
			name_len,
			&actual_len,
			(GLint*)&sp->size,
			&sp->type,
			(GLchar*)name
		);
		sp->loc = glGetUniformLocation(s->prog, (GLchar*)name);

		if (actual_len == 0 || sp->loc == -1) {
			errf("failed to query uniform %d", u);
			goto error;
		}

		// copy obtained name
		char *name_copy = malloc(name_len + 1);
		name_copy[name_len]= 0;
		strncpy(name_copy, name, name_len);
		sp->name = name_copy;
	}

	return 1;

error:
	free(s->params);
	s->params = NULL;
	s->param_count = 0;
	return 0;
}

struct Shader*
shader_new(GLuint vert_src, GLuint frag_src)
{
	GLenum gl_err = GL_NO_ERROR;
	GLuint prog = 0;
	struct Shader *shader = NULL;

	// create shader program
	prog = glCreateProgram();
	if (!prog) {
		errf(
			"failed to create shader program (OpenGL error %d)",
			glGetError()
		);
		goto error;
	}

	// attach shaders and link the program
	glAttachShader(prog, vert_src);
	glAttachShader(prog, frag_src);
	glLinkProgram(prog);
	if ((gl_err = glGetError()) != GL_NO_ERROR) {
		errf("failed to link shader program (OpenGL error %d)", gl_err);
		goto error;
	}

	// retrieve link status
	int status = GL_FALSE;
	glGetProgramiv(prog, GL_LINK_STATUS, &status);
	if (status == GL_FALSE) {
		// retrieve link log
		int log_len;
		glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &log_len);
		char log[log_len];
		glGetProgramInfoLog(prog, log_len, NULL, log);

		errf("failed to link shader: %s", log);
		goto error;
	}

	shader = malloc(sizeof(struct Shader));
	shader->prog = prog;
	if (!init_shader_params(shader)) {
		err("failed to initialize shader params table");
		goto error;
	}

	return shader;

error:
	shader_free(shader);
	return NULL;
}

void
shader_free(struct Shader *s)
{
	if (s) {
		free(s->params);
		free(s);
	}
}

int
shader_use(struct Shader *s)
{
	assert(s != NULL);

	glUseProgram(s->prog);

#ifdef DEBUG
	GLenum gl_err;
	if ((gl_err = glGetError()) != GL_NO_ERROR) {
		errf(
			"failed to make shader %d active (OpenGL error %d)",
			s->prog,
			gl_err
		);
		return 0;
	}
#endif

	return 1;
}

const struct ShaderParam*
shader_get_param(struct Shader *s, const char *name)
{
	assert(s != NULL);
	assert(name != NULL);

	// FIXME: implement a hash table for this
	for (GLuint p = 0; p < s->param_count; p++) {
		struct ShaderParam *sp = s->params + p;
		if (strcmp(sp->name, name) == 0)
			return sp;
	}
	return NULL;
}

int
shader_set_param_mat(const struct ShaderParam *p, size_t count, Mat *m)
{
	assert(p != NULL);
	assert(m != NULL);

	if (p->type != GL_FLOAT_MAT4) {
		errf("shader param %s is not of matrix type", p->name);
		return 0;
	} else if (count > p->size) {
		errf("shader param %s value size too big", p->name);
		return 0;
	}
	glUniformMatrix4fv(p->loc, count, GL_TRUE, (float*)m);
	return 1;
}

int
shader_set_param_vec(const struct ShaderParam *p, size_t count, Vec *v)
{
	assert(p != NULL);
	assert(v != NULL);

	if (p->type != GL_FLOAT_VEC4) {
		errf("shader param %s is not of vector type", p->name);
		return 0;
	} else if (count > p->size) {
		errf("shader param %s value size too big", p->name);
		return 0;
	}

	glUniform4fv(p->loc, count, (float*)v);
	return 1;
}

int
shader_set_param_int(const struct ShaderParam *p, size_t count, int *i)
{
	assert(p != NULL);
	assert(i != NULL);

	if (p->type != GL_INT) {
		errf("shader param %s is not of integer type", p->name);
		return 0;
	} else if (count > p->size) {
		errf("shader param %s value size too big", p->name);
		return 0;
	}

	glUniform1iv(p->loc, count, i);
	return 1;
}

int
shader_set_param_float(const struct ShaderParam *p, size_t count, float *f)
{
	assert(p != NULL);
	assert(f != NULL);

	if (p->type != GL_FLOAT) {
		errf("shader param %s is not of float type", p->name);
		return 0;
	} else if (count > p->size) {
		errf("shader param %s value size too big", p->name);
		return 0;
	}

	glUniform1fv(p->loc, count, f);
	return 1;
}
