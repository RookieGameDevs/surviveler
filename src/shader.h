#pragma once

#include <GL/glew.h>

GLuint
shader_new(const char *vert_src, const char *frag_src);

GLuint
shader_load_and_compile(const char *vert_shader, const char *frag_shader);

int
shader_use(GLuint prog);
