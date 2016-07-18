#pragma once

#include <Python.h>  // must be first
#include <anim.h>
#include <mesh.h>
#include <shader.h>

typedef struct _PyVecObject {
	PyObject_HEAD
	Vec vec;
} PyVecObject;

typedef struct _PyMatObject {
	PyObject_HEAD
	Mat mat;
} PyMatObject;

typedef struct _PyMeshDataObject {
	PyObject_HEAD
	struct MeshData *mesh_data;
	PyMatObject *transform;
	PyObject *animations;
} PyMeshDataObject;

typedef struct _PyMeshObject {
	PyObject_HEAD
	struct Mesh *mesh;
} PyMeshObject;

typedef struct _PyAnimationObject {
	PyObject_HEAD
	struct Animation *anim;
	PyMeshDataObject *container;
} PyAnimationObject;

typedef struct _PyAnimationInstanceObject {
	PyObject_HEAD
	struct AnimationInstance *inst;
	size_t joint_count;
	PyObject *joint_transforms;
	PyObject *skin_transforms;
	PyAnimationObject *ref;
} PyAnimationInstanceObject;

typedef struct _PyShaderSourceObject {
	PyObject_HEAD
	GLuint source;;
} PyShaderSourceObject;

typedef struct _PyShaderObject {
	PyObject_HEAD
	struct Shader *shader;
	PyObject *vert;
	PyObject *frag;
	PyObject *params;
} PyShaderObject;

typedef struct _PyArrayObject {
	PyObject_HEAD
	size_t len;
	size_t size;
	void *data;
	PyObject **items;
	PyTypeObject *type;
} PyArrayObject;

typedef struct _PyShaderParamObject {
	PyObject_HEAD
	PyObject *shader;
	const struct ShaderParam *param;
} PyShaderParamObject;

extern PyTypeObject py_mesh_data_type;
extern PyTypeObject py_mesh_type;
extern PyTypeObject py_animation_type;
extern PyTypeObject py_animation_instance_type;
extern PyTypeObject py_shader_type;
extern PyTypeObject py_shader_source_type;
extern PyTypeObject py_shader_param_type;
extern PyTypeObject py_array_type;
extern PyTypeObject py_vec_type;
extern PyTypeObject py_mat_type;

char*
strfmt(const char *fmt, ...);

void
raise_pyerror(void);
