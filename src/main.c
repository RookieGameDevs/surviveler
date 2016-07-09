#include "anim.h"
#include "matlib.h"
#include "mesh.h"
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

// skeleton pose transform matrix palette
static Mat *pose_transforms = NULL;

// mesh to render
static struct MeshData *mesh_data = NULL;
static struct Mesh *mesh = NULL;

// animation trigger
static bool animate = false;

// global animation timer
static float time = 0.0f;

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
load_model(const char *filename)
{
	mesh_data = mesh_data_from_file(filename);
	if (!mesh_data)
		return 0;

	mesh = mesh_new(mesh_data);
	if (!mesh)
		goto error;

	if (mesh_data->skeleton &&
	    !(pose_transforms = malloc(sizeof(Mat) * mesh_data->skeleton->joint_count)))
		goto error;

	return 1;

error:
	mesh_data_free(mesh_data);
	return 0;
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
	time += dt;

	mat_ident(&modelview);
	mat_lookat(
		&modelview,
		5, 5, 5, // eye
		0, 0, 0, // target
		0, 1, 0  // up
	);

	mat_ident(&transform);

	// play the animation
	if (animate) {
		if (mesh_data->anim_count > 0) {
			anim_compute_pose(
				&mesh_data->animations[0],
				time,
				pose_transforms
			);
		}
		printf("t = %.4fs\n", time);
	}

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

	loc = glGetUniformLocation(shader, "animate");
	glUniform1i(loc, animate);

	if (animate && mesh_data->anim_count > 0) {
		loc = glGetUniformLocation(shader, "joints");
		if (loc < 0) {
			fprintf(stderr, "no 'joints' uniform defined\n");
			return 0;
		};
		glUniformMatrix4fv(
			loc,
			mesh_data->skeleton->joint_count,
			GL_TRUE,
			(float*)pose_transforms
		);
	}

	// draw the model
	if (!mesh_render(mesh))
		return 0;

	glFlush();

	return 1;
}

int
main(int argc, char *argv[])
{
	if (argc != 2) {
		fprintf(stderr, "expected model file name\n");
		return 1;
	}

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

	if (!load_model(argv[1]))
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

				case SDLK_SPACE:
					animate = !animate;
					time = 0.0f;
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

	mesh_free(mesh);
	mesh_data_free(mesh_data);

	return 0;
}
