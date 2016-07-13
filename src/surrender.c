#include "surrender.h"
#include <stdio.h>

int
surrender_init(void)
{
	glewExperimental = GL_TRUE;
	if (glewInit() != 0) {
		fprintf(stderr, "failed to initialize GLEW");
		return 0;
	}
	glGetError(); // silence any errors produced during GLEW initialization
	return 1;
}

void
surrender_shutdown(void)
{
	return;
}
