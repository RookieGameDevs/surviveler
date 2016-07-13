#include "common.h"

extern int
register_anim(PyObject *module);

extern int
register_mesh(PyObject *module);

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

	register_anim(m);
	register_mesh(m);

	return m;
}
