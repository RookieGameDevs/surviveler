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

extern PyTypeObject py_mesh_data_type;
extern PyTypeObject py_mesh_type;

char*
strfmt(const char *fmt, ...);

void
raise_pyerror(void);
