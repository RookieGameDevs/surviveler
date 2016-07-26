#pragma once

/* Third party dependencies */
#include <GL/glew.h>
#include <SDL.h>

/* Project headers */
#include "anim.h"
#include "mesh.h"
#include "shader.h"
#include "matlib.h"

int
surrender_init(unsigned int width, unsigned int height);

int
surrender_render(void);

void
surrender_shutdown(void);
