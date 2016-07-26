#include "common.h"
#include <error.h>
#include <string.h>
#include <structmember.h>

static int
py_shader_init(PyObject *self, PyObject *args, PyObject *kwargs)
{
	Py_ssize_t len = PySequence_Length(args);
	if (args < 0) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a sequence of shader sources"
		);
		return -1;
	}

	PyShaderObject *shader_o = (PyShaderObject*)self;
	shader_o->sources = malloc(sizeof(PyObject*) * len);
	memset(shader_o->sources, 0, sizeof(PyObject*) * len);
	shader_o->source_count = len;

	// initialize the array of shader sources from which the shader program will
	// be created;
	// also store them in the python object and increase the reference, in order
	// to ensure they're alive as long as the dependant shader objects live
	GLuint sources[len];
	for (Py_ssize_t i = 0; i < len; i++) {
		PyObject *item = PySequence_GetItem(args, i);
		if (!PyObject_TypeCheck(item, &py_shader_source_type)) {
			PyErr_Format(
				PyExc_ValueError,
				"argument %d is not a shader source object",
				i + 1
			);
			return -1;
		}

		sources[i] = ((PyShaderSourceObject*)item)->source;
		shader_o->sources[i] = item;
		Py_INCREF(item);
	}

	struct Shader *shader = shader_new(sources, (unsigned)len);
	if (!shader) {
		PyErr_SetString(
			PyExc_ValueError,
			"failed to create shader program"
		);
		return -1;
	}
	shader_o->shader = shader;

	// initialize shader parameters dictionary
	shader_o->params = PyDict_New();
	for (unsigned int p = 0; p < shader->param_count; p++) {
		struct ShaderParam *sp = shader->params + p;
		PyShaderParamObject *param_o = PyObject_New(
			PyShaderParamObject,
			&py_shader_param_type
		);
		param_o->param = sp;
		param_o->shader = self;
		Py_INCREF(self);

		PyDict_SetItemString(
			shader_o->params,
			sp->name,
			(PyObject*)param_o
		);
	}

	// initialize shader class instance attributes dictionary
	shader_o->dict = PyDict_New();
	PyDict_SetItemString(shader_o->dict, "prog", PyLong_FromLong(shader->prog));

	return 0;
}

static void
py_shader_free(PyObject *self)
{
	PyShaderObject *shader_o = (PyShaderObject*)self;
	shader_free(shader_o->shader);
	Py_XDECREF(shader_o->params);
	for (Py_ssize_t i = 0; i < shader_o->source_count; i++) {
		Py_XDECREF(shader_o->sources[i]);
	}
}

static PyObject*
py_shader_use(PyObject *self)
{
	PyShaderObject *shader_o = (PyShaderObject*)self;
	if (!shader_use(shader_o->shader)) {
		error_print_tb();
		error_clear();
		PyErr_SetString(
			PyExc_ValueError,
			"shader binding failed"
		);
		return NULL;
	}
	Py_RETURN_NONE;
}

static Py_ssize_t
py_shader_len(PyObject *self)
{
	PyShaderObject *shader = (PyShaderObject*)self;
	return shader->shader->param_count;
}

static PyShaderParamObject*
get_shader_param(PyObject *self, PyObject *key)
{
	if (!PyUnicode_Check(key)) {
		PyErr_SetString(
			PyExc_TypeError,
			"expected string key"
		);
		return NULL;
	}

	PyShaderObject *shader = (PyShaderObject*)self;
	PyShaderParamObject *sp = NULL;
	sp = (PyShaderParamObject*)PyDict_GetItem(shader->params, key);
	if (!sp) {
		PyErr_Format(
			PyExc_KeyError,
			"no such shader parameter '%s'",
			PyUnicode_AsUTF8(key)
		);
	}

	return sp;
}

static PyObject*
py_shader_get_item(PyObject *self, PyObject *key)
{
	return (PyObject*)get_shader_param(self, key);
}

static int
py_shader_set_item(PyObject *self, PyObject *key, PyObject *val)
{
	PyShaderParamObject *sp = get_shader_param(self, key);
	if (!sp)
		return -1;
	return py_shader_param_set(sp, val) ? 0 : -1;
}

static PyMethodDef py_shader_methods[] = {
	{ "use", (PyCFunction)py_shader_use, METH_NOARGS,
	  "Make the shader active in the rendering pipeline." },
	{ NULL }
};

static PyMappingMethods py_shader_mapping_methods = {
	.mp_length = py_shader_len,
	.mp_subscript = py_shader_get_item,
	.mp_ass_subscript = py_shader_set_item
};

PyTypeObject py_shader_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.Shader",
	.tp_doc = "Shader.",
	.tp_basicsize = sizeof(PyShaderObject),
	.tp_itemsize = 0,
	.tp_dictoffset = offsetof(PyShaderObject, dict),
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_shader_free,
	.tp_new = PyType_GenericNew,
	.tp_init = py_shader_init,
	.tp_print = NULL,
	.tp_getattr = NULL,
	.tp_setattr = NULL,
	.tp_repr = NULL,
	.tp_as_number = NULL,
	.tp_as_sequence = NULL,
	.tp_as_mapping = &py_shader_mapping_methods,
	.tp_as_buffer = NULL,
	.tp_as_async = NULL,
	.tp_hash = NULL,
	.tp_call = NULL,
	.tp_str = NULL,
	.tp_getattro = PyObject_GenericGetAttr,
	.tp_setattro = PyObject_GenericSetAttr,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = py_shader_methods,
	.tp_getset = NULL
};

int
register_shader(PyObject *module)
{
	// register Shader type
	if (PyType_Ready(&py_shader_type) < 0 ||
	    PyModule_AddObject(module, "Shader", (PyObject*)&py_shader_type) < 0)
		raise_pyerror();

	return 1;
}
