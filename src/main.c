#include "matlib.h"
#include <GL/glew.h>
#include <SDL.h>
#include <stdbool.h>
#include <stdio.h>

#define VIEWPORT_WIDTH  1024
#define VIEWPORT_HEIGHT 768

#define VERT_SHADER "data/default.vert"
#define FRAG_SHADER "data/default.frag"

enum {
	PERSPECTIVE,
	ORTHOGRAPHIC
};

static int projection_mode = ORTHOGRAPHIC;

// modelview matrix
static Mat projection;

// modelview matrix
static Mat modelview;

// object transform matrix
static Mat transform;

// model
static GLfloat vertices[] = {
	+0.5, +0.5, +0.5,
	-0.5, +0.5, +0.5,
	-0.5, -0.5, +0.5,
	+0.5, -0.5, +0.5,
	+0.5, +0.5, -0.5,
	-0.5, +0.5, -0.5,
	-0.5, -0.5, -0.5,
	+0.5, -0.5, -0.5
};

static GLuint indices[] = {
	// front face
	0, 1, 2,
	0, 2, 3,
	// back face
	7, 5, 4,
	7, 6, 5,
	// top face
	0, 4, 1,
	1, 4, 5,
	// bottom face
	7, 3, 2,
	7, 2, 6,
	// left face
	4, 0, 3,
	4, 3, 7,
	// right face
	5, 2, 1,
	5, 6, 2
};

static GLuint vao;

enum {
	VERTEX_BUFFER,
	INDEX_BUFFER,
	BUF_COUNT
};
static GLuint buffers[BUF_COUNT];

static GLuint shader;

static GLenum
has_glerror()
{
	GLenum error;
	if ((error = glGetError()) != GL_NO_ERROR) {
		fprintf(stderr, "OpenGL error: %d\n", error);
		return 1;
	}
	return 0;
}

static int
all_ui(const unsigned int *array, size_t len)
{
	for (size_t i = 0; i < len; i++)
		if (!array[i])
			return 0;
	return 1;
}

static int
load_model()
{
	glGenVertexArrays(1, &vao);
	if (!vao || has_glerror()) {
		fprintf(stderr, "VAO generation failed\n");
		return 0;
	}
	glBindVertexArray(vao);

	glGenBuffers(BUF_COUNT, buffers);
	if (!all_ui(buffers, BUF_COUNT) || has_glerror()) {
		fprintf(stderr, "VAO generation failed\n");
		return 0;
	}

	glBindBuffer(GL_ARRAY_BUFFER, buffers[VERTEX_BUFFER]);
	glBufferData(
		GL_ARRAY_BUFFER,
		sizeof(vertices),
		vertices,
		GL_STATIC_DRAW
	);
	if (has_glerror()) {
		fprintf(stderr, "vertex buffer initialization failed\n");
		return 0;
	}

	glEnableVertexAttribArray(0);
	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, (void*)(0));

	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, buffers[INDEX_BUFFER]);
	glBufferData(
		GL_ELEMENT_ARRAY_BUFFER,
		sizeof(indices),
		indices,
		GL_STATIC_DRAW
	);
	if (has_glerror()) {
		fprintf(stderr, "index buffer initialization failed\n");
		return 0;
	}

	glBindVertexArray(0);

	return 1;
}

static int
load_shader()
{
	const char *files[2] = {
		VERT_SHADER,
		FRAG_SHADER
	};
	GLenum types[2] = {
		GL_VERTEX_SHADER,
		GL_FRAGMENT_SHADER
	};
	GLuint shaders[2];

	GLuint prog = glCreateProgram();
	if (!prog || has_glerror()) {
		fprintf(stderr, "failed to create shader program\n");
		return 0;
	}

	for (int i = 0; i < 2; i++) {
		// open file for reading
		FILE *fp = fopen(files[i], "r");
		if (!fp) {
			fprintf(stderr, "failed to open '%s'\n", files[i]);
			return 0;
		}

		// read file size and allocate a buffer for its contents
		fseek(fp, 0, SEEK_END);
		size_t len = ftell(fp);
		rewind(fp);
		char *src = malloc(len + 1);
		if (!src) {
			fprintf(stderr, "not enough memory for '%s'\n", files[i]);
			goto error;
		}
		src[len] = 0;  // NUL-terminator

		// read the file
		if (fread(src, 1, len, fp) != len) {
			fprintf(stderr, "failed to read '%s'\n", files[i]);
			goto error;
		}

		// create the shader
		shaders[i] = glCreateShader(types[i]);
		if (!shaders[i] || has_glerror()) {
			fprintf(stderr, "failed to create shader object\n");
			goto error;
		}

		// set source and compile it
		glShaderSource(shaders[i], 1, (const char**)&src, NULL);
		glCompileShader(shaders[i]);

		int status;
		glGetShaderiv(shaders[i], GL_COMPILE_STATUS, &status);
		if (status == GL_FALSE || has_glerror()) {
			int log_len;
			glGetShaderiv(shaders[i], GL_INFO_LOG_LENGTH, &log_len);
			char log[log_len];
			glGetShaderInfoLog(shaders[i], log_len, NULL, log);
			fprintf(
				stderr,
				"failed to compile %s: %s\n",
				files[i], log
			);
			goto error;
		}

		// attach the shader to the program
		glAttachShader(prog, shaders[i]);

		free(src);
		fclose(fp);
		continue;

error:
		free(src);
		fclose(fp);
		return 0;
	}

	// link the program
	glLinkProgram(prog);
	if (has_glerror()) {
		fprintf(stderr, "failed to link shader program\n");
		return 0;
	}

	int status;
	glGetProgramiv(prog, GL_LINK_STATUS, &status);
	if (status == GL_FALSE) {
		int log_len;
		glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &log_len);
		char log[log_len];
		glGetProgramInfoLog(prog, log_len, NULL, log);
		fprintf(stderr, "failed to link shader: %s\n", log);
		return 0;
	}

	shader = prog;

	return 1;
}

static int
setup()
{
	float aspect = VIEWPORT_HEIGHT / (float)VIEWPORT_WIDTH;
	float fov = 5.0;
	if (projection_mode == PERSPECTIVE) {
		mat_persp(
			&projection,
			fov * 10,
			1.0 / aspect,
			1,
			fov * 2
		);
	} else {
		mat_ortho(
			&projection,
			-fov,
			+fov,
			+fov * aspect,
			-fov * aspect,
			0,
			fov * 2
		);
	}

	glClearColor(0.3, 0.3, 0.3, 1.0);

	glEnable(GL_DEPTH_TEST);

	glEnable(GL_CULL_FACE);
	glCullFace(GL_BACK);

	return 1;
}

static int
update(float dt)
{
	static float angle = 0;

	angle += dt * M_PI / 4.0f;
	if (angle >= 2 * M_PI)
		angle -= 2 * M_PI;

	mat_ident(&modelview);
	mat_lookat(
		&modelview,
		5, 5, 5,
		0, 0, 0,
		0, 1, 0
	);

	Vec axis = vec(0, 1, 0, 0);
	mat_ident(&transform);
	mat_rotate(&transform, &axis, angle);

	return 1;
}

static int
render()
{
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

	// make the shader active
	glUseProgram(shader);
	if (has_glerror()) {
		fprintf(stderr, "failed to activate shader\n");
		return 0;
	}

	// set uniforms
	int loc;

	loc = glGetUniformLocation(shader, "projection");
	glUniformMatrix4fv(loc, 1, GL_TRUE, projection.data);

	loc = glGetUniformLocation(shader, "modelview");
	glUniformMatrix4fv(loc, 1, GL_TRUE, modelview.data);

	loc = glGetUniformLocation(shader, "transform");
	glUniformMatrix4fv(loc, 1, GL_TRUE, transform.data);

	// draw the model
	glBindVertexArray(vao);
	glDrawElements(
		GL_TRIANGLES,
		sizeof(indices) / sizeof(GLuint),
		GL_UNSIGNED_INT,
		(void*)(0)
	);

	if (has_glerror()) {
		fprintf(stderr, "failed to render model\n");
		return 0;
	}

	glFlush();

	return 1;
}

int
main(int argc, char *argv[])
{
	// initialize SDL
	if (SDL_Init(SDL_INIT_EVERYTHING) != 0) {
		fprintf(stderr, "failed to initialize SDL: %s", SDL_GetError());
		return 1;
	}

	// create an OpenGL window
	SDL_Window *window = SDL_CreateWindow(
		"OpenGL demo",
		SDL_WINDOWPOS_CENTERED,
		SDL_WINDOWPOS_CENTERED,
		VIEWPORT_WIDTH,
		VIEWPORT_HEIGHT,
		SDL_WINDOW_OPENGL
	);
	if (!window) {
		fprintf(stderr, "failed to create OpenGL window\n");
		return 1;
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

	SDL_GLContext *context = SDL_GL_CreateContext(window);
	if (!context) {
		fprintf(stderr, "failed to initialize OpenGL context\n");
		return 1;
	}

	// initialize GLEW
	glewExperimental = GL_TRUE;
	if (glewInit()) {
		fprintf(stderr, "failed to initialize GLEW");
		return 1;
	}
	// clear any error flags which might have been left by GLEW
	// initialization routine
	glGetError();

	printf("OpenGL version: %s\n", glGetString(GL_VERSION));
	printf("GLSL version: %s\n", glGetString(GL_SHADING_LANGUAGE_VERSION));

	if (!setup())
		return 0;

	if (!load_model())
		return 0;

	if (!load_shader())
		return 0;

	SDL_Event evt;

	bool run = true;
	Uint32 last_update = 0;
	while (run) {
		while (SDL_PollEvent(&evt)) {
			if (evt.type == SDL_KEYUP) {
				switch (evt.key.keysym.sym) {
				case SDLK_q:
				case SDLK_ESCAPE:
					run = false;
					break;

				case SDLK_p:
					if (projection_mode == ORTHOGRAPHIC)
						projection_mode = PERSPECTIVE;
					else
						projection_mode = ORTHOGRAPHIC;
					run &= setup();
					break;
				}

			}
		}

		Uint32 now = SDL_GetTicks();
		if (last_update == 0)
			last_update = now;
		float dt = (now - last_update) / 1000.0f;
		last_update = now;

		run &= update(dt);

		run &= render();
		SDL_GL_SwapWindow(window);
	}

	return 0;
}
