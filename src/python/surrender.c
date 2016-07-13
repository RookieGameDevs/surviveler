#include "common.h"

extern int
register_animation(PyObject *module);

extern int
register_mesh_data(PyObject *module);

extern int
register_mesh(PyObject *module);

int
register_animation_instance(PyObject *module);

struct PyModuleDef surrender_module = {
	PyModuleDef_HEAD_INIT,
	"surrender",
	NULL,
	-1,
	NULL
};

/**
 * Module initialization function.
 */
PyMODINIT_FUNC
PyInit_surrender(void)
{

	PyObject *m = PyModule_Create(&surrender_module);
	if (!m)
		fprintf(stderr, "Failed to create module\n");

	register_animation(m);
	register_mesh_data(m);
	register_mesh(m);
	register_animation_instance(m);

	return m;
}
