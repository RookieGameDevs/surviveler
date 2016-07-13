#pragma once

#include <Python.h>  // must be first
#include <mesh.h>
#include <anim.h>

typedef struct _PyMeshDataObject {
	PyObject_HEAD
	struct MeshData *mesh_data;
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

typedef struct _PyVecObject {
	PyObject_HEAD
	Vec vec;
} PyVecObject;

typedef struct _PyMatObject {
	PyObject_HEAD
	Mat mat;
} PyMatObject;

extern PyTypeObject py_mesh_data_type;
extern PyTypeObject py_mesh_type;
extern PyTypeObject py_animation_type;
extern PyTypeObject py_animation_instance_type;
extern PyTypeObject py_animation_instance_type;
extern PyTypeObject py_vec_type;
extern PyTypeObject py_mat_type;

char*
strfmt(const char *fmt, ...);

void
raise_pyerror(void);
