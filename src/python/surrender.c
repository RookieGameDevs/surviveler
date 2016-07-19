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

extern int
register_matlib(PyObject *module);

extern int
register_array(PyObject *module);

extern int
register_shader_param(PyObject *module);

extern int
register_shader_source(PyObject *module);

extern int
register_shader(PyObject *module);

static PyObject*
py_surrender_init(PyObject *unused, PyObject *args);

static PyObject*
py_surrender_shutdown(void);

static PyObject*
py_surrender_render(void);

static PyMethodDef functions[] = {
	{"init", (PyCFunction)py_surrender_init, METH_VARARGS,
	 "Initialize renderer library."},
	{"shutdown", (PyCFunction)py_surrender_shutdown, METH_NOARGS,
	 "Shutdown renderer library."},
	{"render", (PyCFunction)py_surrender_render, METH_NOARGS,
	 "Render a frame."},
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
py_surrender_init(PyObject *unused, PyObject *args)
{
	unsigned int w, h;
	if (!PyArg_ParseTuple(args, "II", &w, &h)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected width and height"
		);
		return NULL;
	} else if (!surrender_init(w, h)) {
		PyErr_SetString(
			PyExc_ValueError,
			"surrender initialization failed"
		);
		return NULL;
	}
	Py_RETURN_NONE;
}

static PyObject*
py_surrender_render(void)
{
	if (!surrender_render()) {
		PyErr_SetString(
			PyExc_ValueError,
			"error occurred during rendering"
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

	register_matlib(m);
	register_animation(m);
	register_mesh_data(m);
	register_mesh(m);
	register_animation_instance(m);
	register_array(m);
	register_shader_source(m);
	register_shader_param(m);
	register_shader(m);

	return m;
}
