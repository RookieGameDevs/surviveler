#include "surrender.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

static SDL_Window *window = NULL;
static SDL_GLContext *context = NULL;
static int initialized = 0;
static int registered_at_exit = 0;

int
surrender_init(unsigned int width, unsigned int height)
{
	if (initialized)
		surrender_shutdown();

	// initialize SDL
	if (SDL_Init(SDL_INIT_EVERYTHING) != 0) {
		fprintf(stderr, "failed to initialize SDL: %s", SDL_GetError());
		return 0;
	}

	// create window
	window = SDL_CreateWindow(
		"OpenGL demo",
		SDL_WINDOWPOS_CENTERED,
		SDL_WINDOWPOS_CENTERED,
		width,
		height,
		SDL_WINDOW_OPENGL
	);
	if (!window) {
		fprintf(stderr, "failed to create OpenGL window\n");
		goto cleanup;
	}

	// initialize OpenGL context
	SDL_GL_SetAttribute(
		SDL_GL_CONTEXT_PROFILE_MASK,
		SDL_GL_CONTEXT_PROFILE_CORE
	);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
	SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
	SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);

	context = SDL_GL_CreateContext(window);
	if (!context) {
		fprintf(stderr, "failed to initialize OpenGL context\n");
		goto cleanup;
	}

	// initialize GLEW
	glewExperimental = GL_TRUE;
	if (glewInit() != 0) {
		fprintf(stderr, "failed to initialize GLEW");
		goto cleanup;
	}
	glGetError(); // silence any errors produced during GLEW initialization

	printf("OpenGL version: %s\n", glGetString(GL_VERSION));
	printf("GLSL version: %s\n", glGetString(GL_SHADING_LANGUAGE_VERSION));
	printf("GLEW version: %s\n", glewGetString(GLEW_VERSION));

	initialized = 1;
	if (!registered_at_exit) {
		atexit(surrender_shutdown);
		registered_at_exit = 1;
	}
	return 1;

cleanup:
	surrender_shutdown();
	return 0;
}

int
surrender_render(void)
{
	assert(initialized);
	glFlush();
	SDL_GL_SwapWindow(window);
	return 1;
}

void
surrender_shutdown(void)
{
	if (context) {
		SDL_GL_DeleteContext(context);
		context = NULL;
	}
	if (window) {
		SDL_DestroyWindow(window);
		window = NULL;
	}

	SDL_Quit();
	initialized = 0;
}
