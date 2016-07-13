#include "common.h"
#include <mesh.h>
#include <string.h>

static PyObject*
py_mesh_data_from_file(PyObject *unused, PyObject *filename_o);

static void
py_mesh_data_free(PyObject *self);

static PyObject*
py_mesh_data_get_animation(PyObject *self, PyObject *name);

static PyObject*
py_mesh_data_get_animation_names(PyObject *self);

static PyMethodDef py_mesh_data_methods[] = {
	{ "from_file", (PyCFunction)py_mesh_data_from_file, METH_O | METH_STATIC,
	  "Load mesh data from file." },
	{ "get_animation", (PyCFunction)py_mesh_data_get_animation, METH_O,
	  "Retrieve animation by name." },
	{ "get_animation_names", (PyCFunction)py_mesh_data_get_animation_names, METH_NOARGS,
	  "Retrieve the list of available animation names." },
	{ NULL }
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
	.tp_getset = NULL
};

static PyObject*
py_mesh_data_from_file(PyObject *__unused, PyObject *filename_o)
{
	if (!PyUnicode_Check(filename_o)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected a filename string"
		);
		return NULL;
	}

	PyMeshDataObject *result = PyObject_New(PyMeshDataObject, &py_mesh_data_type);
	result->mesh_data = mesh_data_from_file((char*)PyUnicode_1BYTE_DATA(filename_o));
	if (!result->mesh_data) {
		Py_DECREF(result);
		Py_RETURN_NONE;
	}
	return (PyObject*)result;
}

static PyObject*
py_mesh_data_get_animation(PyObject *self, PyObject *name_o)
{
	if (!PyUnicode_Check(name_o)) {
		PyErr_SetString(
			PyExc_ValueError,
			"expected animation name string"
		);
		return NULL;
	}

	struct MeshData *md = ((PyMeshDataObject*)self)->mesh_data;
	const char *name = (char*)PyUnicode_1BYTE_DATA(name_o);
	struct Animation *anim = NULL;
	for (size_t i = 0; i < md->anim_count; i++) {
		if (strcmp(md->animations[i].name, name) == 0) {
			anim = &md->animations[i];
			break;
		}
	}

	if (!anim) {
		char *errmsg = strfmt("animation '%s' not found", name);
		PyErr_SetString(
			PyExc_ValueError,
			errmsg
		);
		free(errmsg);
		return NULL;
	}

	PyAnimationObject *obj = PyObject_New(PyAnimationObject, &py_animation_type);
	obj->anim = anim;
	obj->container = (PyMeshDataObject*)self;
	Py_INCREF(self);

	return (PyObject*)obj;
}

static PyObject*
py_mesh_data_get_animation_names(PyObject *self)
{
	struct MeshData *md = ((PyMeshDataObject*)self)->mesh_data;
	PyObject *list = PyList_New(md->anim_count);
	for (size_t i = 0; i < md->anim_count; i++) {
		PyList_SetItem(list, i, PyUnicode_FromString(md->animations[i].name));
	}
	return list;
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
