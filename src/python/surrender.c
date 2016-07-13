#include "common.h"
#include "surrender.h"

extern int
register_animation(PyObject *module);

extern int
register_mesh_data(PyObject *module);

extern int
register_mesh(PyObject *module);

extern int
register_animation_instance(PyObject *module);

static PyObject*
py_surrender_init(void);

static PyObject*
py_surrender_shutdown(void);

static PyMethodDef functions[] = {
	{"init", (PyCFunction)py_surrender_init, METH_NOARGS,
	 "Initialize renderer library."},
	{"shutdown", (PyCFunction)py_surrender_shutdown, METH_NOARGS,
	 "Shutdown renderer library."},
	{NULL}
};

struct PyModuleDef surrender_module = {
	PyModuleDef_HEAD_INIT,
	"surrender",
	NULL,
	-1,
	functions
};

static PyObject*
py_surrender_init(void)
{
	if (!surrender_init()) {
		PyErr_SetString(
			PyExc_ValueError,
			"surrender initialization failed"
		);
		return NULL;
	}
	Py_RETURN_NONE;
}

static PyObject*
py_surrender_shutdown(void)
{
	surrender_shutdown();
	Py_RETURN_NONE;
}

/**
 * Module initialization function.
 */
PyMODINIT_FUNC
PyInit_surrender(void)
{

	PyObject *m = PyModule_Create(&surrender_module);
	if (!m)
		fprintf(stderr, "Failed to create module\n");

	register_animation(m);
	register_mesh_data(m);
	register_mesh(m);
	register_animation_instance(m);

	return m;
}
