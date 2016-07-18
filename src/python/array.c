#include "common.h"
#include <string.h>
#include <structmember.h>

static void
py_array_free(PyObject *self)
{
	PyArrayObject *src_o = (PyArrayObject*)self;
	free(src_o->data);
}

static Py_ssize_t
py_array_size(PyObject *self)
{
	return ((PyArrayObject*)self)->size;
}

static PyObject*
py_array_get_item(PyObject *self, Py_ssize_t i)
{
	// TODO
	Py_RETURN_NONE;
}

static PyObject*
py_array_repr(PyObject *self)
{
	PyArrayObject *array_o = (PyArrayObject*)self;
	return PyUnicode_FromFormat("<Array(%s)>", array_o->array_type->tp_name);
}

static PySequenceMethods py_array_sequence = {
	.sq_length = py_array_size,
	.sq_item = py_array_get_item,
	.sq_concat = NULL,
	.sq_repeat = NULL,
	.sq_ass_item = NULL,
	.sq_contains = NULL,
	.sq_inplace_concat = NULL,
	.sq_inplace_repeat = NULL
};

PyTypeObject py_array_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.Array",
	.tp_doc = "Contiguous array container.",
	.tp_basicsize = sizeof(PyArrayObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_array_free,
	.tp_new = PyType_GenericNew,
	.tp_init = NULL,
	.tp_print = NULL,
	.tp_getattr = NULL,
	.tp_setattr = NULL,
	.tp_repr = py_array_repr,
	.tp_as_number = NULL,
	.tp_as_sequence = &py_array_sequence,
	.tp_as_mapping = NULL,
	.tp_as_buffer = NULL,
	.tp_as_async = NULL,
	.tp_hash = NULL,
	.tp_call = NULL,
	.tp_str = NULL,
	.tp_getattro = PyObject_GenericGetAttr,
	.tp_setattro = PyObject_GenericSetAttr,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = NULL,
	.tp_members = NULL,
	.tp_getset = NULL
};

int
register_array(PyObject *module)
{
	// register array type
	if (PyType_Ready(&py_array_type) < 0 ||
	    PyModule_AddObject(module, "Array", (PyObject*)&py_array_type) < 0)
		raise_pyerror();

	return 1;
}
