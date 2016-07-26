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

static int
set_float(const struct ShaderParam *p, PyObject *float_o)
{
	float v = PyFloat_AsDouble(float_o);
	return shader_set_param_float(p, 1, &v);
}

static int
set_int(const struct ShaderParam *p, PyObject *int_o)
{
	int v = PyLong_AsLong(int_o);
	return shader_set_param_int(p, 1, &v);
}

static int
set_array(const struct ShaderParam *p, PyArrayObject *array)
{
	if (array->type == &py_mat_type)
		return shader_set_param_mat(p, array->len, (Mat*)array->data);
	else if (array->type == &py_vec_type)
		return shader_set_param_vec(p, array->len, (Vec*)array->data);
	errf("unsupported array type '%s'", array->type->tp_name);
	return 0;
}

int
py_shader_param_set(PyShaderParamObject *self, PyObject *val)
{
	const struct ShaderParam *p = self->param;

	int ok = 0;
	if (PyObject_TypeCheck(val, &py_mat_type)) {
		ok = set_mat(p, val);
	} else if (PyObject_TypeCheck(val, &py_vec_type)) {
		ok = set_vec(p, val);
	} else if (PyFloat_Check(val)) {
		ok = set_float(p, val);
	} else if (PyLong_Check(val)) {
		ok = set_int(p, val);
	} else if (PyObject_TypeCheck(val, &py_array_type)) {
		ok = set_array(p, (PyArrayObject*)val);
	} else {
		PyErr_Format(
			PyExc_TypeError,
			"unsupported type '%s' for shader param '%s'",
			Py_TYPE(val)->tp_name,
			p->name
		);
		return 0;
	}

	if (!ok) {
		PyErr_Format(
			PyExc_RuntimeError,
			"failed to set shader param '%s'",
			p->name
		);
		error_print_tb();
		error_clear();
		return 0;
	}

	return 1;
}

static PyObject*
py_shader_param_set_method(PyObject *self, PyObject *val)
{
	if (!py_shader_param_set((PyShaderParamObject*)self, val))
		return NULL;
	Py_RETURN_NONE;
}

static PyMethodDef py_shader_param_methods[] = {
	{ "set", (PyCFunction)py_shader_param_set_method, METH_O,
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

