#include "common.h"
#include <mesh.h>

static PyObject*
py_mesh_data_from_file(PyObject *unused, PyObject *filename_o);

static void
py_mesh_data_free(PyObject *self);

typedef struct _PyMeshDataObject {
	PyObject_HEAD
	struct MeshData *mesh_data;
} PyMeshDataObject;

static PyMethodDef py_mesh_data_methods[] = {
	{ "from_file", (PyCFunction)py_mesh_data_from_file, METH_O | METH_STATIC,
	  "Load mesh data from file." },
	{ NULL }
};

static PyTypeObject py_mesh_data_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.MeshData",
	.tp_doc = "Mesh data container.",
	.tp_basicsize = sizeof(PyMeshDataObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_mesh_data_free,
	.tp_new = PyType_GenericNew,
	.tp_init = NULL,
	.tp_print = NULL,
	.tp_getattr = NULL,
	.tp_setattr = NULL,
	.tp_repr = NULL,
	.tp_as_number = NULL,
	.tp_as_sequence = NULL,
	.tp_as_mapping = NULL,
	.tp_as_buffer = NULL,
	.tp_as_async = NULL,
	.tp_hash = NULL,
	.tp_call = NULL,
	.tp_str = NULL,
	.tp_getattro = NULL,
	.tp_setattro = NULL,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = py_mesh_data_methods,
	.tp_getset = NULL
};

static PyObject*
py_mesh_data_from_file(PyObject *__unused, PyObject *filename_o)
{
	if (!PyUnicode_Check(filename_o)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a filename string"
		);
		return NULL;
	}

	PyMeshDataObject *result = PyObject_New(PyMeshDataObject, &py_mesh_data_type);
	result->mesh_data = mesh_data_from_file((char*)PyUnicode_1BYTE_DATA(filename_o));
	if (!result->mesh_data) {
		Py_DECREF(result);
		Py_RETURN_NONE;
	}
	return (PyObject*)result;
}

static void
py_mesh_data_free(PyObject *self)
{
	PyMeshDataObject *md_o = (PyMeshDataObject*)self;
	mesh_data_free(md_o->mesh_data);
}

int
register_mesh(PyObject *module)
{
	// register MeshData type
	if (PyType_Ready(&py_mesh_data_type) < 0 ||
	    PyModule_AddObject(module, "MeshData", (PyObject*)&py_mesh_data_type) < 0)
		raise_pyerror();

	return 1;
}
