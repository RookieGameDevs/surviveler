#include "error.h"
#include "ioutils.h"
#include "shader.h"
#include <stdio.h>
#include <stdlib.h>

static GLuint
compile_shader(const char *src, GLenum type)
{
	GLenum gl_err = GL_NO_ERROR;

	// create the shader
	GLuint shader = glCreateShader(type);
	if (!shader) {
		errf("failed to create shader (OpenGL error %d)", gl_err);
		goto error;
	}

	// set shader and compile it
	glShaderSource(shader, 1, (const char**)&src, NULL);
	glCompileShader(shader);

	int status = GL_FALSE;
	glGetShaderiv(shader, GL_COMPILE_STATUS, &status);
	if (status == GL_FALSE) {
		// fetch compile log
		int log_len;
		glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &log_len);
		char log[log_len];
		glGetShaderInfoLog(shader, log_len, NULL, log);

		errf("failed to compile shader: %s", log);
		goto error;
	}

	return shader;

error:
	if (shader != 0)
		glDeleteShader(shader);
	return 0;
}

GLuint
shader_load_and_compile(const char *vert_shader, const char *frag_shader)
{
	char *vert_src;
	if (!file_read(vert_shader, &vert_src))
		return 0;

	char *frag_src;
	if (!file_read(frag_shader, &frag_src)) {
		free(vert_src);
		return 0;
	}

	return shader_new(vert_src, frag_src);
}

GLuint
shader_new(const char *vert_src, const char *frag_src)
{
	GLenum gl_err = GL_NO_ERROR;
	GLuint prog = 0;

	// compile shader shaders
	GLuint shaders[2];
	const char *sources[2] = { vert_src, frag_src, };
	GLenum types[2] = { GL_VERTEX_SHADER, GL_FRAGMENT_SHADER };
	for (int i = 0; i < 2; i++) {
		if (!(shaders[i] = compile_shader(sources[i], types[i])))
			goto error;
	}

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
	for (int i = 0; i < 2; i++)
		glAttachShader(prog, shaders[i]);
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

	return prog;

error:
	for (int i = 0; i < 2; i++)
		glDeleteShader(shaders[i]);
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
