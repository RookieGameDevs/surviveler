#include "common.h"
#include <anim.h>

static int
py_animation_instance_init(PyObject *self, PyObject *args, PyObject *kwargs);

static void
py_animation_instance_free(PyObject *self);

static PyObject*
py_animation_instance_play(PyObject *self, PyObject *args);

static PyMethodDef py_animation_instance_methods[] = {
	{ "play", (PyCFunction)py_animation_instance_play, METH_VARARGS,
	  "Advance the animation by given time delta." },
	{ NULL }
};

PyTypeObject py_animation_instance_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.AnimationInstance",
	.tp_doc = "Animation instance class.",
	.tp_basicsize = sizeof(PyAnimationInstanceObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_animation_instance_free,
	.tp_new = PyType_GenericNew,
	.tp_init = py_animation_instance_init,
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
	.tp_methods = py_animation_instance_methods,
	.tp_getset = NULL
};

static int
py_animation_instance_init(PyObject *self, PyObject *args, PyObject *kwargs)
{
	PyAnimationObject *anim_o;
	if (!PyArg_ParseTuple(args, "O", &anim_o) ||
	    !PyObject_TypeCheck(anim_o, &py_animation_type)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected an Animation object"
		);
		return -1;
	}

	struct AnimationInstance *inst = anim_new_instance(anim_o->anim);
	if (!inst) {
		PyErr_SetString(
			PyExc_ValueError,
			"Animation instance object creation failed"
		);
		return -1;
	}
	Py_INCREF(anim_o);

	((PyAnimationInstanceObject*)self)->ref = anim_o;
	((PyAnimationInstanceObject*)self)->inst = inst;
	return 0;
}

static void
py_animation_instance_free(PyObject *self)
{
	PyAnimationInstanceObject *inst_o = (PyAnimationInstanceObject*)self;
	Py_DECREF(inst_o->ref);
	anim_free_instance(inst_o->inst);
}

static PyObject*
py_animation_instance_play(PyObject *self, PyObject *args)
{
	float dt;
	if (!PyArg_ParseTuple(args, "f", &dt)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a time delta as float"
		);
		return NULL;
	}
	if (!anim_play(((PyAnimationInstanceObject*)self)->inst, dt)) {
		PyErr_SetString(
			PyExc_ValueError,
			"animation play failed"
		);
		return NULL;
	}
	Py_RETURN_NONE;
}

int
register_animation_instance(PyObject *module)
{
	// register Animation type
	if (PyType_Ready(&py_animation_instance_type) < 0 ||
	    PyModule_AddObject(module, "AnimationInstance", (PyObject*)&py_animation_instance_type) < 0)
		raise_pyerror();

	return 1;
}
