#include "common.h"
#include <mesh.h>
#include <string.h>
#include <structmember.h>

static PyObject*
py_mesh_data_from_file(PyObject *unused, PyObject *arg);

static PyObject*
py_mesh_data_from_buffer(PyObject *unused, PyObject *arg);

static void
py_mesh_data_free(PyObject *self);

static PyMethodDef py_mesh_data_methods[] = {
	{ "from_file", (PyCFunction)py_mesh_data_from_file, METH_O | METH_STATIC,
	  "Load mesh data from file." },
	{ "from_buffer", (PyCFunction)py_mesh_data_from_buffer, METH_O | METH_STATIC,
	  "Load mesh data from buffer object." },
	{ NULL }
};

static PyMemberDef py_mesh_data_members[] = {
	{ "transform", T_OBJECT, offsetof(PyMeshDataObject, transform), READONLY,
	  "Root transform." },
	{ "animations", T_OBJECT, offsetof(PyMeshDataObject, animations), READONLY,
	  "List of animations." },
	{ NULL },
};

PyTypeObject py_mesh_data_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "surrender.MeshData",
	.tp_doc = "Mesh data container.",
	.tp_basicsize = sizeof(PyMeshDataObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = py_mesh_data_free,
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
	.tp_getattro = NULL,
	.tp_setattro = NULL,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = py_mesh_data_methods,
	.tp_members = py_mesh_data_members,
	.tp_getset = NULL
};

static PyObject*
make_object(struct MeshData *md)
{
	PyMeshDataObject *md_o = PyObject_New(PyMeshDataObject, &py_mesh_data_type);
	md_o->mesh_data = md;

	// setup animations dict
	md_o->animations = PyDict_New();
	for (size_t i = 0; i < md->anim_count; i++) {
		PyAnimationObject *anim_o = PyObject_New(PyAnimationObject, &py_animation_type);
		anim_o->anim = &md->animations[i];
		anim_o->container = md_o;

		PyDict_SetItemString(md_o->animations, md->animations[i].name, (PyObject*)anim_o);

		Py_INCREF(md_o);
	}

	// initialize transform attribute
	md_o->transform = PyObject_New(PyMatObject, &py_mat_type);
	md_o->transform->mat = md->transform;

	return (PyObject*)md_o;
}

static PyObject*
py_mesh_data_from_file(PyObject *unused, PyObject *arg)
{
	if (!PyUnicode_Check(arg)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a filename string"
		);
		return NULL;
	}

	struct MeshData *md = mesh_data_from_file((char*)PyUnicode_1BYTE_DATA(arg));
	if (!md) {
		PyErr_SetString(
			PyExc_ValueError,
			"Mesh data object creation failed"
		);
		return NULL;
	}

	return make_object(md);
}

static PyObject*
py_mesh_data_from_buffer(PyObject *unused, PyObject *arg)
{
	Py_buffer buf;
	if (!PyObject_CheckBuffer(arg)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a buffer-like object"
		);
		return NULL;
	} else if (PyObject_GetBuffer(arg, &buf, PyBUF_SIMPLE) < 0) {
		PyErr_SetString(
			PyExc_ValueError,
			"failed to acquire buffer object"
		);
		return NULL;
	}

	struct MeshData *md = mesh_data_from_buffer(buf.buf, buf.len);
	if (!md) {
		PyErr_SetString(
			PyExc_ValueError,
			"Mesh data object creation failed"
		);
		return NULL;
	}

	return make_object(md);
}

static void
py_mesh_data_free(PyObject *self)
{
	PyMeshDataObject *md_o = (PyMeshDataObject*)self;
	mesh_data_free(md_o->mesh_data);
}

int
register_mesh_data(PyObject *module)
{
	// register MeshData type
	if (PyType_Ready(&py_mesh_data_type) < 0 ||
	    PyModule_AddObject(module, "MeshData", (PyObject*)&py_mesh_data_type) < 0)
		raise_pyerror();

	return 1;
}
