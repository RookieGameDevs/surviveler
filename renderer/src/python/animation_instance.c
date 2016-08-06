#include "common.h"
#include <structmember.h>

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

static PyMemberDef py_animation_instance_members[] = {
	{ "joint_count", T_INT, offsetof(PyAnimationInstanceObject, joint_count), READONLY,
	  "Number of joints." },
	{ "joint_transforms", T_OBJECT, offsetof(PyAnimationInstanceObject, joint_transforms), READONLY,
	  "Joint transformations array." },
	{ "skin_transforms", T_OBJECT, offsetof(PyAnimationInstanceObject, skin_transforms), READONLY,
	  "Skin transformations array." },
	{ NULL },
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
	.tp_getattro = PyObject_GenericGetAttr,
	.tp_setattro = PyObject_GenericSetAttr,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = py_animation_instance_methods,
	.tp_members = py_animation_instance_members,
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

	PyAnimationInstanceObject *inst_o = (PyAnimationInstanceObject*)self;
	inst_o->joint_count = inst->anim->skeleton->joint_count;
	inst_o->joint_transforms = (PyObject*)py_array_from_c_buffer(
		self,
		inst->joint_transforms,
		inst_o->joint_count,
		sizeof(Mat),
		&py_mat_type
	);
	inst_o->skin_transforms = (PyObject*)py_array_from_c_buffer(
		self,
		inst->skin_transforms,
		inst_o->joint_count,
		sizeof(Mat),
		&py_mat_type
	);
	if (!(inst_o->joint_transforms && inst_o->skin_transforms))
		return -1;

	inst_o->ref = anim_o;
	inst_o->inst = inst;

	return 0;
}

static void
py_animation_instance_free(PyObject *self)
{
	PyAnimationInstanceObject *inst_o = (PyAnimationInstanceObject*)self;
	Py_XDECREF(inst_o->joint_transforms);
	Py_XDECREF(inst_o->skin_transforms);
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

	PyAnimationInstanceObject *inst_o = (PyAnimationInstanceObject*)self;
	struct AnimationInstance *inst = inst_o->inst;

	int ok = 0;

	// acquire transforms array buffers
	Py_buffer jbuf, sbuf;
	int jbuf_ok = PyObject_GetBuffer(inst_o->joint_transforms, &jbuf, PyBUF_WRITABLE) == 0;
	int sbuf_ok = PyObject_GetBuffer(inst_o->skin_transforms, &sbuf, PyBUF_WRITABLE) == 0;
	if (!(jbuf_ok && sbuf_ok)) {
		PyErr_SetString(
			PyExc_ValueError,
			"failed to acquire animation instance transform array buffers"
		);
		goto cleanup;
	}

	// advance animation by given time delta
	if (!anim_play(inst, dt)) {
		PyErr_SetString(
			PyExc_ValueError,
			"animation play failed"
		);
		goto cleanup;
	}
	ok = 1;

cleanup:
	if (jbuf_ok)
		PyBuffer_Release(&jbuf);
	if (sbuf_ok)
		PyBuffer_Release(&sbuf);
	if (ok)
		Py_RETURN_NONE;
	return NULL;  // error
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
