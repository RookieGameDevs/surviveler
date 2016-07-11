#include "ioutils.h"
#include "shader.h"
#include <stdio.h>
#include <stdlib.h>

static GLuint
compile_source(const char *filename, GLenum type)
{
	GLenum gl_err = GL_NO_ERROR;

#define has_gl_error() (gl_err = glGetError()) != GL_NO_ERROR

	char *data = NULL;
	if (!file_read(filename, &data))
		return 0;

	// create the shader
	GLuint source = glCreateShader(type);
	if (!source || has_gl_error()) {
		fprintf(stderr, "failed to create shader source object\n");
		goto error;
	}

	// set source and compile it
	glShaderSource(source, 1, (const char**)&data, NULL);
	glCompileShader(source);

	int status;
	glGetShaderiv(source, GL_COMPILE_STATUS, &status);
	if (status == GL_FALSE || has_gl_error()) {
		int log_len;
		glGetShaderiv(source, GL_INFO_LOG_LENGTH, &log_len);
		char log[log_len];
		glGetShaderInfoLog(source, log_len, NULL, log);
		fprintf(
			stderr,
			"failed to compile %s: %s\n",
			filename,
			log
		);
		goto error;
	}

#undef has_gl_error

cleanup:
	free(data);

	return source;

error:
	if (gl_err != GL_NO_ERROR)
		fprintf(stderr, "OpenGL error %d\n", gl_err);
	if (source != 0)
		glDeleteShader(source);
	source = 0;
	goto cleanup;
}

GLuint
shader_load_and_compile(const char *vert_shader, const char *frag_shader)
{
	GLenum gl_err = GL_NO_ERROR;

#define has_gl_error() (gl_err = glGetError()) != GL_NO_ERROR

	GLuint prog = 0;

	// compile shader sources
	GLuint sources[2];
	const char *files[2] = { vert_shader, frag_shader, };
	GLenum types[2] = { GL_VERTEX_SHADER, GL_FRAGMENT_SHADER };
	for (int i = 0; i < 2; i++) {
		if (!(sources[i] = compile_source(files[i], types[i])))
			goto error;
	}

	// create shader program
	prog = glCreateProgram();
	if (!prog || has_gl_error()) {
		fprintf(stderr, "failed to create shader program\n");
		goto error;
	}

	// attach shaders and link the program
	for (int i = 0; i < 2; i++)
		glAttachShader(prog, sources[i]);
	glLinkProgram(prog);
	if (has_gl_error()) {
		fprintf(stderr, "failed to link shader program\n");
		goto error;
	}

	// retrieve link status
	int status;
	glGetProgramiv(prog, GL_LINK_STATUS, &status);
	if (status == GL_FALSE) {
		int log_len;
		glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &log_len);
		char log[log_len];
		glGetProgramInfoLog(prog, log_len, NULL, log);
		fprintf(stderr, "failed to link shader: %s\n", log);
		goto error;
	}

#undef has_gl_error

	printf("loaded shader program from %s %s\n", vert_shader, frag_shader);

	return prog;

error:
	if (gl_err != GL_NO_ERROR)
		fprintf(stderr, "OpenGL error %d\n", gl_err);

	for (int i = 0; i < 2; i++)
		glDeleteShader(sources[i]);
	glDeleteProgram(prog);
	return 0;
}

int
shader_use(GLuint prog)
{
	GLenum gl_err;
	glUseProgram(prog);
	if ((gl_err = glGetError()) != GL_NO_ERROR) {
		fprintf(
			stderr,
			"failed to make shader %d active\n"
			"OpenGL error %d\n",
			prog,
			gl_err
		);
		return 0;
	}
	return 1;
}
