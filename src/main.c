#include "anim.h"
#include "matlib.h"
#include "mesh.h"
#include "shader.h"
#include <GL/glew.h>
#include <SDL.h>
#include <stdbool.h>
#include <stdio.h>

#define VIEWPORT_WIDTH  1024
#define VIEWPORT_HEIGHT 768

#define MODEL_VERT "data/default.vert"
#define MODEL_FRAG "data/default.frag"
#define JOINT_VERT "data/joint.vert"
#define JOINT_FRAG "data/joint.frag"

enum CameraType {
	PERSPECTIVE,
	ORTHOGRAPHIC,
	CAMERA_TYPE_COUNT
};

enum RenderMode {
	WIREFRAME,
	SOLID,
	RENDER_MODE_COUNT
};

// modelview matrix
static Mat projection;

// modelview matrix
static Mat modelview;

// object transform matrix
static Mat transform;

// meshes
static struct MeshData *joint_mesh_data = NULL;
static struct MeshData *mesh_data = NULL;
static struct Mesh *joint_mesh = NULL;
static struct Mesh *mesh = NULL;

// animation instance to play
static struct AnimationInstance *anim_inst = NULL;

// controls
static struct {
	bool play_animation;
	enum CameraType cam_type;
	enum RenderMode rndr_mode;
} controls = {
	.play_animation = false,
	.cam_type = ORTHOGRAPHIC,
	.rndr_mode = SOLID
};

// shaders
static GLuint model_shader = 0;
static GLuint joint_shader = 0;

static int
load_mesh(const char *filename, struct MeshData **md, struct Mesh **m)
{
	*md = NULL;
	*m = NULL;

	if(!(*md = mesh_data_from_file(filename)))
		return 0;

	if (!(*m = mesh_new(*md))) {
		mesh_data_free(*md);
		return 0;
	}

	printf("loaded %s\n", filename);

	return 1;
}

static int
load_shaders()
{
	model_shader = shader_load_and_compile(MODEL_VERT, MODEL_FRAG);
	joint_shader = shader_load_and_compile(JOINT_VERT, JOINT_FRAG);
	return model_shader && joint_shader;
}

static int
setup()
{
	float aspect = VIEWPORT_HEIGHT / (float)VIEWPORT_WIDTH;
	float fov = 5.0;
	if (controls.cam_type % CAMERA_TYPE_COUNT == PERSPECTIVE) {
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

	switch (controls.rndr_mode % RENDER_MODE_COUNT) {
	case WIREFRAME:
		glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
		break;
	case SOLID:
		glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
		break;
	}

	return 1;
}

static int
update(float dt)
{
	mat_ident(&modelview);
	mat_lookat(
		&modelview,
		5, 5, 5, // eye
		0, 0, 0, // target
		0, 1, 0  // up
	);

	transform = mesh_data->transform;

	// play the animation
	if (controls.play_animation && anim_inst) {
		anim_play(anim_inst, dt);
		printf("t = %.4fs\n", anim_inst->time);
	}

	return 1;
}

static int
render()
{
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

	int loc;

	// draw skeleton joints
	if (anim_inst && controls.play_animation) {
		if (!shader_use(joint_shader))
			return 0;

		loc = glGetUniformLocation(joint_shader, "projection");
		glUniformMatrix4fv(loc, 1, GL_TRUE, projection.data);

		loc = glGetUniformLocation(joint_shader, "modelview");
		glUniformMatrix4fv(loc, 1, GL_TRUE, modelview.data);

		for (int j = 0; j < anim_inst->anim->skeleton->joint_count; j++) {
			loc = glGetUniformLocation(joint_shader, "transform");
			Mat joint_transform;
			mat_mul(&transform, &anim_inst->joint_transforms[j], &joint_transform);
			glUniformMatrix4fv(
				loc,
				1,
				GL_TRUE,
				joint_transform.data
			);

			if (!mesh_render(joint_mesh))
				return 0;
		}
	}

	// update model shader uniforms
	if (!shader_use(model_shader))
		return 0;

	loc = glGetUniformLocation(model_shader, "projection");
	glUniformMatrix4fv(loc, 1, GL_TRUE, projection.data);

	loc = glGetUniformLocation(model_shader, "modelview");
	glUniformMatrix4fv(loc, 1, GL_TRUE, modelview.data);

	loc = glGetUniformLocation(model_shader, "transform");
	glUniformMatrix4fv(loc, 1, GL_TRUE, transform.data);

	loc = glGetUniformLocation(model_shader, "animate");
	glUniform1i(loc, controls.play_animation);

	if (controls.play_animation && anim_inst > 0) {
		loc = glGetUniformLocation(model_shader, "joints");
		if (loc < 0) {
			fprintf(stderr, "no 'joints' uniform defined\n");
			return 0;
		};
		glUniformMatrix4fv(
			loc,
			mesh_data->skeleton->joint_count,
			GL_TRUE,
			(float*)anim_inst->skin_transforms
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

	// load mesh and create animation instance
	if (!load_mesh(argv[1], &mesh_data, &mesh))
		return 0;
	if (mesh_data->anim_count > 0 &&
	    !(anim_inst = anim_new_instance(&mesh_data->animations[0])))
		return 0;

	// load joint mesh
	if (!load_mesh("data/joint.mesh", &joint_mesh_data, &joint_mesh))
		return 0;

	if (!load_shaders())
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
					controls.cam_type++;
					run &= setup();
					break;

				case SDLK_r:
					controls.rndr_mode++;
					run &= setup();
					break;

				case SDLK_SPACE:
					if (anim_inst) {
						controls.play_animation = !controls.play_animation;
						anim_inst->time = 0.0f;
					}
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
	mesh_free(joint_mesh);
	mesh_data_free(joint_mesh_data);

	return 0;
}
