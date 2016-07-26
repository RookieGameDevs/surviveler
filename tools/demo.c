#include "error.h"
#include "surrender.h"
#include <signal.h>
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
	int play_animation;
	enum CameraType cam_type;
	enum RenderMode rndr_mode;
} controls = {
	.play_animation = false,
	.cam_type = ORTHOGRAPHIC,
	.rndr_mode = SOLID
};

// shaders
static struct {
	struct Shader *shader;
	GLuint vert, frag;
	const struct ShaderParam *projection;
	const struct ShaderParam *modelview;
	const struct ShaderParam *transform;
	const struct ShaderParam *animate;
	const struct ShaderParam *joints;
} model_shader = { NULL };

static struct {
	struct Shader *shader;
	GLuint vert, frag;
	const struct ShaderParam *projection;
	const struct ShaderParam *modelview;
	const struct ShaderParam *transform;
} joint_shader = { NULL };

static int
load_mesh(const char *filename, struct MeshData **md, struct Mesh **m)
{
	*md = NULL;
	*m = NULL;

	if(!(*md = mesh_data_from_file(filename))) {
		errf("failed to load mesh %s", filename);
		return 0;
	}

	if (!(*m = mesh_new(*md))) {
		mesh_data_free(*md);
		return 0;
	}

	printf("loaded %s\n", filename);

	return 1;
}

static void
print_shader_info(const char *name, struct Shader *s)
{
	printf("Shader %s params table:\n", name);
	for (unsigned int i = 0; i < s->param_count; i++) {
		struct ShaderParam sp = s->params[i];
		printf("  %-20s (loc=%d, size=% d, type=%d)\n", sp.name, sp.loc, sp.size, sp.type);
	}
}

static int
load_shaders()
{
	if (!(model_shader.vert = shader_compile_file(MODEL_VERT)))
		return 0;
	printf("loaded %s\n", MODEL_VERT);
	if (!(model_shader.frag = shader_compile_file(MODEL_FRAG)))
		return 0;
	printf("loaded %s\n", MODEL_FRAG);

	GLuint sources[2] = {
		model_shader.vert,
		model_shader.frag
	};
	if (!(model_shader.shader = shader_new(sources, 2)))
		return 0;

	print_shader_info("model", model_shader.shader);
	model_shader.projection = shader_get_param(model_shader.shader, "projection");
	model_shader.modelview = shader_get_param(model_shader.shader, "modelview");
	model_shader.transform = shader_get_param(model_shader.shader, "transform");
	model_shader.joints = shader_get_param(model_shader.shader, "joints[0]");
	model_shader.animate = shader_get_param(model_shader.shader, "animate");

	if (!(joint_shader.vert = shader_compile_file(JOINT_VERT)))
		return 0;
	printf("loaded %s\n", JOINT_VERT);
	if (!(joint_shader.frag = shader_compile_file(JOINT_FRAG)))
		return 0;
	printf("loaded %s\n", JOINT_FRAG);

	sources[0] = joint_shader.vert;
	sources[1] = joint_shader.frag;
	if (!(joint_shader.shader = shader_new(sources, 2)))
		return 0;

	print_shader_info("joint", joint_shader.shader);
	joint_shader.projection = shader_get_param(joint_shader.shader, "projection");
	joint_shader.modelview = shader_get_param(joint_shader.shader, "modelview");
	joint_shader.transform = shader_get_param(joint_shader.shader, "transform");

	return model_shader.shader && joint_shader.shader;
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

	// draw skeleton joints
	if (anim_inst && controls.play_animation) {
		if (!shader_use(joint_shader.shader))
			return 0;

		shader_set_param_mat(joint_shader.projection, 1, &projection);
		shader_set_param_mat(joint_shader.modelview, 1, &modelview);

		Mat joint_transform;
		for (int j = 0; j < anim_inst->anim->skeleton->joint_count; j++) {
			mat_mul(
				&transform,
				&anim_inst->joint_transforms[j],
				&joint_transform
			);
			shader_set_param_mat(
				joint_shader.transform,
				1,
				&joint_transform
			);
			if (!mesh_render(joint_mesh))
				return 0;
		}
	}

	// update model shader uniforms
	if (!shader_use(model_shader.shader))
		return 0;

	shader_set_param_mat(model_shader.projection, 1, &projection);
	shader_set_param_mat(model_shader.modelview, 1, &modelview);
	shader_set_param_mat(model_shader.transform, 1, &transform);
	shader_set_param_int(model_shader.animate, 1, &controls.play_animation);

	if (controls.play_animation && anim_inst > 0) {
		shader_set_param_mat(
			model_shader.joints,
			mesh_data->skeleton->joint_count,
			anim_inst->skin_transforms
		);
	}

	// draw the model
	if (!mesh_render(mesh))
		return 0;

	surrender_render();

	return 1;
}

int
main(int argc, char *argv[])
{
	if (argc != 2) {
		fprintf(stderr, "expected model file name\n");
		return 1;
	}

	// print error traceback on abort
	signal(SIGABRT, (sig_t)error_print_tb);

	int ok = surrender_init(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
	if (!ok)
		goto cleanup;

	// setup OpenGL context and cameras
	if (!(ok = setup()))
		goto cleanup;

	// load mesh data
	if (!(ok = load_mesh(argv[1], &mesh_data, &mesh)))
		goto cleanup;

	// create animation instance
	if (mesh_data->anim_count > 0 &&
	    !(anim_inst = anim_new_instance(&mesh_data->animations[0]))) {
		ok = 0;
		goto cleanup;
	}

	// load joint mesh
	if (!(ok = load_mesh("data/joint.mesh", &joint_mesh_data, &joint_mesh)))
		goto cleanup;

	// load shaders
	if (!(ok = load_shaders()))
		goto cleanup;

	// main loop
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
	}

cleanup:
	if (!ok) {
		error_print_tb();
		error_clear();
	}

	mesh_free(mesh);
	mesh_data_free(mesh_data);
	mesh_free(joint_mesh);
	mesh_data_free(joint_mesh_data);

	shader_free_source(model_shader.vert);
	shader_free_source(model_shader.frag);
	shader_free(model_shader.shader);

	shader_free_source(joint_shader.vert);
	shader_free_source(joint_shader.frag);
	shader_free(joint_shader.shader);

	surrender_shutdown();
	return 0;
}
