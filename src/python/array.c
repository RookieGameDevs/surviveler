#include "common.h"
#include <string.h>
#include <structmember.h>

static int
get_item_buffer(PyArrayObject *array, size_t i, Py_buffer *buf)
{
	// acquire item object buffer
	if (PyObject_GetBuffer(array->items[i], buf, PyBUF_WRITABLE) < 0) {
		PyErr_Format(
			PyExc_RuntimeError,
			"failed to acquire write access to %s buffer",
			array->type->tp_name
		);
		return 0;
	} else if (buf->len != array->size) {
		PyErr_Format(
			PyExc_RuntimeError,
			"buffer size does not match %s object size (%d != %d)",
			array->type->tp_name,
			buf->len,
			array->size
		);
		PyBuffer_Release(buf);
		return 0;
	}
	return 1;
}

static int
update_item(PyArrayObject *array, size_t i)
{
	Py_buffer buf;
	if (get_item_buffer(array, i, &buf)) {
		memcpy(buf.buf, array->data + array->size * i, buf.len);
		PyBuffer_Release(&buf);
		return 1;
	}
	return 0;
}

static int
update_array(PyArrayObject *array, size_t i)
{
	Py_buffer buf;
	if (get_item_buffer(array, i, &buf)) {
		memcpy(array->data + array->size * i, buf.buf, buf.len);
		PyBuffer_Release(&buf);
		return 1;
	}
	return 0;
}

static int
py_array_init(PyObject *self, PyObject *args, PyObject *kwargs)
{
	size_t len = 0, size = 0;
	PyTypeObject *t;
	if (!PyArg_ParseTuple(args, "O!II", &PyType_Type, &t, &len, &size) ||
	    t->tp_as_buffer == NULL) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected buffer compatible type, length and size"
		);
		return -1;
	}

	PyArrayObject *array = (PyArrayObject*)self;
	array->type = t;
	array->len = len;
	array->size = size;
	array->data = NULL;
	array->items = NULL;

	// allocate the array for underlying data
	if (!(array->data = malloc(len * size))) {
		PyErr_SetString(
			PyExc_RuntimeError,
			"out of memory"
		);
		goto error;
	}
	memset(array->data, 0, len * size);

	// allocate an array of mirror objects
	if (!(array->items = malloc(sizeof(PyObject*) * len))) {
		PyErr_SetString(
			PyExc_RuntimeError,
			"out of memory"
		);
		goto error;
	}
	memset(array->items, 0, len * sizeof(PyObject*));

	// initialize mirror items
	for (size_t i = 0; i < len; i++) {
		array->items[i] = PyObject_New(PyObject, t);
		if (!update_item(array, i))
			goto error;
	}

	return 0;

error:
	free(array->data);
	array->data = NULL;
	free(array->items);
	array->items = NULL;
	return -1;
}

static void
py_array_free(PyObject *self)
{
	PyArrayObject *array = (PyArrayObject*)self;
	free(array->data);
	if (array->items) {
		for (size_t i = 0; i < array->len; i++)
			Py_XDECREF(array->items[i]);
	}
	free(array->items);
}

static Py_ssize_t
py_array_size(PyObject *self)
{
	return ((PyArrayObject*)self)->len;
}

static PyObject*
py_array_get_item(PyObject *self, Py_ssize_t i)
{
	PyArrayObject *array = (PyArrayObject*)self;
	if (i >= array->len) {
		PyErr_SetString(
			PyExc_IndexError,
			"out of bounds"
		);
		return NULL;
	}
	PyObject *o = array->items[i];
	Py_INCREF(o);
	return o;
}

static int
py_array_set_item(PyObject *self, Py_ssize_t i, PyObject *v)
{
	PyArrayObject *array = (PyArrayObject*)self;
	if (i >= array->len) {
		PyErr_SetString(
			PyExc_IndexError,
			"out of bounds"
		);
		return -1;
	} else if (!PyObject_TypeCheck(v, array->type)) {
		PyErr_Format(
			PyExc_IndexError,
			"expected a %s instance",
			array->type->tp_name
		);
		return -1;
	}
	Py_DECREF(array->items[i]);
	array->items[i] = v;
	Py_INCREF(v);
	return update_array(array, i) ? 0 : -1;
}

static PyObject*
py_array_repr(PyObject *self)
{
	PyArrayObject *array = (PyArrayObject*)self;
	return PyUnicode_FromFormat(
		"<Array(%s, %d)>",
		array->type->tp_name,
		array->len
	);
}

static int
py_array_getbuffer(PyObject *self, Py_buffer *view, int flags)
{
	PyArrayObject *array = (PyArrayObject*)self;
	return PyBuffer_FillInfo(
		view,
		self,
		array->data,
		array->len * array->size,
		0,
		flags
	);
}

static void
py_array_releasebuffer(PyObject *self, Py_buffer *view)
{
	PyArrayObject *array = (PyArrayObject*)self;

	// update mirror items
	for (size_t i = 0; i < array->len; i++) {
		update_item(array, i);
	}
}

static PyBufferProcs py_array_buf_methods = {
	.bf_getbuffer = py_array_getbuffer,
	.bf_releasebuffer = py_array_releasebuffer,
};

static PySequenceMethods py_array_sequence = {
	.sq_length = py_array_size,
	.sq_item = py_array_get_item,
	.sq_concat = NULL,
	.sq_repeat = NULL,
	.sq_ass_item = py_array_set_item,
	.sq_contains = NULL,
	.sq_inplace_concat = NULL,
	.sq_inplace_repeat = NULL
};

PyTypeObject py_array_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.Array",
	.tp_doc = "Serializable contiguous array of items.",
	.tp_basicsize = sizeof(PyArrayObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_array_free,
	.tp_new = PyType_GenericNew,
	.tp_init = py_array_init,
	.tp_print = NULL,
	.tp_getattr = NULL,
	.tp_setattr = NULL,
	.tp_repr = py_array_repr,
	.tp_as_number = NULL,
	.tp_as_sequence = &py_array_sequence,
	.tp_as_mapping = NULL,
	.tp_as_buffer = &py_array_buf_methods,
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
