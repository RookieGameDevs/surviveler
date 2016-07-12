#ifdef WITH_PYTHON
# include <Python.h>  // must be first
#endif

/**
 * Module definition.
 */
static struct PyModuleDef module = {
	PyModuleDef_HEAD_INIT,
	"surrender.anim",
	NULL,
	-1,
	NULL
};

/**
 * Module initialization function.
 */
PyMODINIT_FUNC
PyInit_anim(void)
{

	PyObject *m = PyModule_Create(&module);
	if (!m)
		raise_pyerror();

	return m;
}
