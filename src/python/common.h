#pragma once

#include <Python.h>  // must be first

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
	PyAnimationObject *ref;
} PyAnimationInstanceObject;

extern PyTypeObject py_mesh_data_type;
extern PyTypeObject py_mesh_type;
extern PyTypeObject py_animation_type;
extern PyTypeObject py_animation_instance_type;

char*
strfmt(const char *fmt, ...);

void
raise_pyerror(void);
