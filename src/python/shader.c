#include "common.h"
#include <string.h>
#include <structmember.h>

static int
py_shader_init(PyObject *self, PyObject *args, PyObject *kwargs)
{
	PyObject *vert_src_o, *frag_src_o;
	if (!PyArg_ParseTuple(args, "OO", &vert_src_o, &frag_src_o) ||
	    !PyObject_TypeCheck(vert_src_o, &py_shader_source_type) ||
	    !PyObject_TypeCheck(frag_src_o, &py_shader_source_type)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected vertex and shader source objects as arguments"
		);
		return -1;
	}

	GLuint vert = ((PyShaderSourceObject*)vert_src_o)->source;
	GLuint frag = ((PyShaderSourceObject*)frag_src_o)->source;

	struct Shader *shader = shader_new(vert, frag);
	if (!shader) {
		PyErr_SetString(
			PyExc_ValueError,
			"failed to create shader program"
		);
		return -1;
	}

	PyShaderObject *shader_o = PyObject_New(PyShaderObject, &py_shader_type);
	shader_o->shader = shader;
	shader_o->vert = vert_src_o;
	shader_o->frag = frag_src_o;
	Py_INCREF(vert_src_o);
	Py_INCREF(frag_src_o);

	shader_o->params = PyDict_New();
	for (unsigned int p = 0; p < shader->param_count; p++) {
		struct ShaderParam *sp = shader->params + p;
		// TODO: add shader params
	}

	return 0;
}

static void
py_shader_free(PyObject *self)
{
	PyShaderObject *shader_o = (PyShaderObject*)self;
	shader_free(shader_o->shader);
	Py_DECREF(shader_o->params);
	Py_DECREF(shader_o->vert);
	Py_DECREF(shader_o->frag);
}

static PyObject*
py_shader_use(PyObject *self, PyObject *args)
{
	// TODO
	return NULL;
}

static PyMethodDef py_shader_methods[] = {
	{ "use", (PyCFunction)py_shader_use, METH_NOARGS,
	  "Make the shader active in the rendering pipeline." },
	{ NULL }
};

static PyMemberDef py_shader_members[] = {
	{ "params", T_OBJECT, offsetof(PyShaderObject, params), READONLY,
	  "Shader parameters mapping." },
	{ NULL },
};

PyTypeObject py_shader_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.Shader",
	.tp_doc = "Shader.",
	.tp_basicsize = sizeof(PyShaderObject),
	.tp_itemsize = 0,
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
	.tp_as_mapping = NULL,
	.tp_as_buffer = NULL,
	.tp_as_async = NULL,
	.tp_hash = NULL,
	.tp_call = NULL,
	.tp_str = NULL,
	.tp_getattro = PyObject_GenericGetAttr,
	.tp_setattro = PyObject_GenericSetAttr,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = py_shader_methods,
	.tp_members = py_shader_members,
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
