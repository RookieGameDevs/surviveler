#include "common.h"
#include <error.h>
#include <shader.h>
#include <string.h>
#include <structmember.h>

static void
py_shader_param_free(PyObject *self)
{
	PyShaderParamObject *param = (PyShaderParamObject*)self;
	Py_DECREF(param->shader);
}

static int
set_mat(const struct ShaderParam *p, PyObject *mat_o)
{
	PyMatObject *mat = (PyMatObject*)mat_o;
	return shader_set_param_mat(p, 1, &mat->mat);
}

static int
set_vec(const struct ShaderParam *p, PyObject *vec_o)
{
	PyVecObject *vec = (PyVecObject*)vec_o;
	return shader_set_param_vec(p, 1, &vec->vec);
}

static PyObject*
py_shader_set_param(PyObject *self, PyObject *val)
{
	const struct ShaderParam *p = ((PyShaderParamObject*)self)->param;

	int ok = 0;
	if (PyObject_TypeCheck(val, &py_mat_type)) {
		ok = set_mat(p, val);
	} else if (PyObject_TypeCheck(val, &py_vec_type)) {
		ok = set_vec(p, val);
	} else {
		PyErr_Format(
			PyExc_ValueError,
			"unsupported type '%s' for shader '%s'",
			Py_TYPE(val)->tp_name,
			p->name
		);
		return NULL;
	}

	if (!ok) {
		PyErr_Format(
			PyExc_ValueError,
			"failed to set shader param '%s'",
			p->name
		);
		error_print_tb();
		error_clear();
	}

	Py_RETURN_NONE;
}

static PyMethodDef py_shader_param_methods[] = {
	{ "set", (PyCFunction)py_shader_set_param, METH_O,
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
	    PyModule_AddObject(module, "ShaderParam", (PyObject*)&py_shader_param_type) < 0)
		raise_pyerror();

	return 1;
}

