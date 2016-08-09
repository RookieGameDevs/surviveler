#include "common.h"
#include <error.h>

static int
py_mesh_init(PyObject *self, PyObject *args, PyObject *kwargs);

static void
py_mesh_free(PyObject *self);

static PyObject*
py_mesh_render(PyObject *self);

static PyMethodDef py_mesh_methods[] = {
	{ "render", (PyCFunction)py_mesh_render, METH_NOARGS,
	  "Render the mesh." },
	{ NULL }
};

PyTypeObject py_mesh_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.Mesh",
	.tp_doc = "Mesh class.",
	.tp_basicsize = sizeof(PyMeshObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_mesh_free,
	.tp_new = PyType_GenericNew,
	.tp_init = py_mesh_init,
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
	.tp_methods = py_mesh_methods,
	.tp_getset = NULL
};

static int
py_mesh_init(PyObject *self, PyObject *args, PyObject *kwargs)
{
	PyObject *md_o;
	if (!PyArg_ParseTuple(args, "O", &md_o) ||
	    !PyObject_TypeCheck(md_o, &py_mesh_data_type)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a MeshData object"
		);
		return -1;
	}

	struct MeshData *md = ((PyMeshDataObject*)md_o)->mesh_data;
	struct Mesh *mesh = mesh_new(md);
	if (!mesh) {
		PyErr_SetString(
			PyExc_ValueError,
			"Mesh object creation failed"
		);
		return -1;
	}

	((PyMeshObject*)self)->mesh = mesh;
	return 0;
}

static void
py_mesh_free(PyObject *self)
{
	PyMeshObject *md_o = (PyMeshObject*)self;
	mesh_free(md_o->mesh);
}

static PyObject*
py_mesh_render(PyObject *self)
{
	if (!mesh_render(((PyMeshObject*)self)->mesh)) {
		error_print_tb();
		error_clear();
		PyErr_SetString(
			PyExc_ValueError,
			"mesh object rendering failed"
		);
		return NULL;
	}
	Py_RETURN_NONE;
}

int
register_mesh(PyObject *module)
{
	// register Mesh type
	if (PyType_Ready(&py_mesh_type) < 0 ||
	    PyModule_AddObject(module, "Mesh", (PyObject*)&py_mesh_type) < 0)
		raise_pyerror();

	return 1;
}
