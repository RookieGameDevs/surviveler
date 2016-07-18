#include "common.h"
#include <error.h>
#include <string.h>
#include <structmember.h>

static PyObject*
make_object(GLuint source)
{
	PyShaderSourceObject *src_o = (PyShaderSourceObject*)PyObject_New(
		PyShaderSourceObject,
		&py_shader_source_type
	);
	src_o->source = source;
	return (PyObject*)src_o;
}

static void
py_shader_source_free(PyObject *self)
{
	PyShaderSourceObject *src_o = (PyShaderSourceObject*)self;
	shader_free_source(src_o->source);
}

static PyObject*
py_shader_source_from_buffer(PyObject *unused, PyObject *args)
{
	int type;
	PyObject *buf_o;
	Py_buffer buf;
	if (!PyArg_ParseTuple(args, "Oi", &buf_o, &type) ||
	    !PyObject_CheckBuffer(buf_o)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a buffer-like object and shader type"
		);
		return NULL;
	} else if (type != GL_FRAGMENT_SHADER || type != GL_VERTEX_SHADER) {
		PyErr_SetString(
			PyExc_ValueError,
			"invalid shader type"
		);
		return NULL;
	} else if (PyObject_GetBuffer(buf_o, &buf, PyBUF_SIMPLE) < 0) {
		PyErr_SetString(
			PyExc_ValueError,
			"failed to acquire buffer object"
		);
		return NULL;
	}

	GLuint src = shader_compile_source(buf.buf, type);
	if (src) {
		PyErr_SetString(
			PyExc_ValueError,
			"failed to compile shader source"
		);
	}
	PyBuffer_Release(&buf);

	return src ? make_object(src) : NULL;
}

static PyObject*
py_shader_source_from_file(PyObject *unused, PyObject *arg)
{
	char *filename;
	if (!PyArg_ParseTuple(arg, "s", &filename)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected shader source file name"
		);
		return NULL;
	}

	GLuint src = shader_compile_file(filename);
	if (!src) {
		PyErr_SetString(
			PyExc_ValueError,
			error_last()
		);
		return NULL;
	}
	return make_object(src);
}

static PyMethodDef py_shader_source_methods[] = {
	{ "from_buffer", (PyCFunction)py_shader_source_from_buffer, METH_VARARGS | METH_STATIC,
	  "Compile a shader source from buffer-like object." },
	{ "from_file", (PyCFunction)py_shader_source_from_file, METH_VARARGS | METH_STATIC,
	  "Compile a shader source from file." },
	{ NULL }
};

PyTypeObject py_shader_source_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.ShaderSource",
	.tp_doc = "Shader source.",
	.tp_basicsize = sizeof(PyShaderSourceObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_shader_source_free,
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
	.tp_getattro = PyObject_GenericGetAttr,
	.tp_setattro = PyObject_GenericSetAttr,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = py_shader_source_methods,
	.tp_members = NULL,
	.tp_getset = NULL
};

int
register_shader_source(PyObject *module)
{
	// register ShaderSource type
	if (PyType_Ready(&py_shader_source_type) < 0 ||
	    PyModule_AddObject(module, "ShaderSource", (PyObject*)&py_shader_source_type) < 0)
		raise_pyerror();

	PyDict_SetItemString(
		py_shader_source_type.tp_dict,
		"FRAGMENT_SHADER",
		Py_BuildValue("i", GL_FRAGMENT_SHADER)
	);
	PyDict_SetItemString(
		py_shader_source_type.tp_dict,
		"VERTEX_SHADER",
		Py_BuildValue("i", GL_VERTEX_SHADER)
	);

	return 1;
}
