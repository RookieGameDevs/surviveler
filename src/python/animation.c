#include "common.h"
#include <anim.h>

static void
py_animation_free(PyObject *self);

static PyObject*
py_animation_play(PyObject *self, PyObject *args);

static PyMethodDef py_animation_methods[] = {
	{ "play", (PyCFunction)py_animation_play, METH_VARARGS,
	  "Advance the animation by given time delta." },
	{ NULL }
};

PyTypeObject py_animation_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surplay.Animation",
	.tp_doc = "Animation class.",
	.tp_basicsize = sizeof(PyAnimationObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_animation_free,
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
	.tp_methods = py_animation_methods,
	.tp_getset = NULL
};

static void
py_animation_free(PyObject *self)
{
	// TODO
}

static PyObject*
py_animation_play(PyObject *self, PyObject *args)
{
	// TODO
	Py_RETURN_NONE;
}

int
register_animation(PyObject *module)
{
	// register Animation type
	if (PyType_Ready(&py_animation_type) < 0 ||
	    PyModule_AddObject(module, "Animation", (PyObject*)&py_animation_type) < 0)
		raise_pyerror();

	return 1;
}
