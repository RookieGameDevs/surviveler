#include "common.h"
#include <string.h>
#include <structmember.h>

static void
py_shader_param_free(PyObject *self)
{
	PyShaderParamObject *src_o = (PyShaderParamObject*)self;
	Py_DECREF(src_o->shader);
}

static PyObject*
py_shader_param_set(PyObject *self, PyObject *val)
{
	PyShaderParamObject *src_o = (PyShaderParamObject*)self;

	return NULL;
}

static PyMethodDef py_shader_param_methods[] = {
	{ "set", (PyCFunction)py_shader_param_set, METH_O,
	  "Set shader parameter." },
	{ NULL }
};

PyTypeObject py_shader_param_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.ShaderParam",
	.tp_doc = "Shader parameter.",
	.tp_basicsize = sizeof(PyShaderParamObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_shader_param_free,
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
	.tp_methods = py_shader_param_methods,
	.tp_members = NULL,
	.tp_getset = NULL
};

int
register_shader_param(PyObject *module)
{
	// register ShaderParam type
	if (PyType_Ready(&py_shader_param_type) < 0 ||
	    PyModule_AddObject(module, "ShaderParam", (PyObject*)&py_array_type) < 0)
		raise_pyerror();

	return 1;
}

