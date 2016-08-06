#include "common.h"

static struct PyModuleDef matlib_module = {
	PyModuleDef_HEAD_INIT,
	"matlib",
	NULL,
	-1,
	NULL
};

#define to_vec(pyobj) (((PyVecObject*)pyobj)->vec)
#define to_vec_ptr(pyobj) (&((PyVecObject*)pyobj)->vec)

static int
py_vec_init(PyObject *self, PyObject *args, PyObject *kwargs);

static PyObject*
py_vec_repr(PyObject *self);

static PyObject*
py_vec_norm(PyObject *self);

static PyObject*
py_vec_mag(PyObject *self);

static PyObject*
py_vec_add(PyObject *self, PyObject *args);

static PyObject*
py_vec_iadd(PyObject *self, PyObject *args);

static PyObject*
py_vec_sub(PyObject *self, PyObject *other);

static PyObject*
py_vec_isub(PyObject *self, PyObject *other);

static PyObject*
py_vec_mul(PyObject *self, PyObject *other);

static PyObject*
py_vec_imul(PyObject *self, PyObject *other);

static PyObject*
py_vec_neg(PyObject *self);

static PyObject*
py_vec_cross(PyObject *unused, PyObject *args);

static PyObject*
py_vec_dot(PyObject *unused, PyObject *args);

static PyObject*
py_vec_getter(PyObject *self, void *offset);

static int
py_vec_setter(PyObject *self, PyObject *arg, void *offset);

static int
py_vec_getbuffer(PyObject *self, Py_buffer *view, int flags);

/**
 * Vec class methods.
 */
static PyMethodDef vec_methods[] = {
	{ "norm", (PyCFunction)py_vec_norm, METH_NOARGS,
	  "Normalize the vector." },
	{ "mag", (PyCFunction)py_vec_mag, METH_NOARGS,
	  "Get vector's magnitude (length) for X, Y, Z components." },
	{ "cross", (PyCFunction)py_vec_cross, METH_O,
	  "Perform cross product between two vectors using X, Y, Z componets." },
	{ "dot", (PyCFunction)py_vec_dot, METH_O,
	  "Perform dot product between two vectors using X, Y, Z components." },
	{ NULL }
};

/**
 * Vec computed attributes.
 */
static PyGetSetDef vec_attrs[] = {
	{ "x", py_vec_getter, py_vec_setter, .closure = (void*)0UL, .doc =
	  "X component" },
	{ "y", py_vec_getter, py_vec_setter, .closure = (void*)1UL, .doc =
	  "Y component" },
	{ "z", py_vec_getter, py_vec_setter, .closure = (void*)2UL, .doc =
	  "Z component" },
	{ "w", py_vec_getter, py_vec_setter, .closure = (void*)3UL, .doc =
	  "W component" },
	{ NULL }
};

/**
 * Vec number methods.
 */
static PyNumberMethods vec_num_methods = {
	.nb_add = py_vec_add,
	.nb_inplace_add = py_vec_iadd,
	.nb_subtract = py_vec_sub,
	.nb_negative = py_vec_neg,
	.nb_inplace_subtract = py_vec_isub,
	.nb_multiply = py_vec_mul,
	.nb_inplace_multiply = py_vec_imul
};

/**
 * Vec buffer methods.
 */
static PyBufferProcs vec_buf_methods = {
	.bf_getbuffer = py_vec_getbuffer,
	.bf_releasebuffer = NULL
};

/**
 * Vec object type definition.
 */
PyTypeObject py_vec_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "matlib.Vec",
	.tp_doc = "Vector with X,Y,Z,W components.",
	.tp_basicsize = sizeof(PyVecObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = NULL,
	.tp_new = PyType_GenericNew,
	.tp_init = py_vec_init,
	.tp_print = NULL,
	.tp_getattr = NULL,
	.tp_setattr = NULL,
	.tp_repr = py_vec_repr,
	.tp_as_number = &vec_num_methods,
	.tp_as_sequence = NULL,
	.tp_as_mapping = NULL,
	.tp_as_buffer = &vec_buf_methods,
	.tp_as_async = NULL,
	.tp_hash = NULL,
	.tp_call = NULL,
	.tp_str = NULL,
	.tp_getattro = NULL,
	.tp_setattro = NULL,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = vec_methods,
	.tp_getset = vec_attrs
};

static PyObject*
py_vec_repr(PyObject *self)
{
	Vec v = to_vec(self);
	char *s = strfmt(
		"Vec(%f, %f, %f, %f)",
		v.data[0],
		v.data[1],
		v.data[2],
		v.data[3]
	);
	PyObject *repr = PyUnicode_FromString(s);
	free(s);

	return repr;
}

static int
py_vec_init(PyObject *self, PyObject *args, PyObject *kwargs)
{
	float data[] = { 0, 0, 0, 0 };
	if (!PyArg_ParseTuple(args, "|ffff", data, data + 1, data + 2, data + 3)) {
		PyErr_SetString(PyExc_RuntimeError, "expected at most 4 floats");
		return -1;
	}
	memcpy(to_vec(self).data, data, sizeof(float) * 4);
	return 0;
}

static PyObject*
py_vec_norm(PyObject *self)
{
	vec_norm(to_vec_ptr(self));
	Py_RETURN_NONE;
}

static PyObject*
py_vec_mag(PyObject *self)
{
	return PyFloat_FromDouble(vec_mag(to_vec_ptr(self)));
}

static PyObject*
py_vec_op_helper(
	PyObject *self,
	PyObject *other,
	void (*scalar_op)(const Vec *a, float scalar, Vec *r_v),
	void (*vector_op)(const Vec *a, const Vec *b, Vec *r_v),
	int in_place
) {
	Vec *v = to_vec_ptr(self);
	Vec r_v;

	if (PyFloat_Check(other) && scalar_op) {
		scalar_op(v, PyFloat_AsDouble(other), &r_v);
	} else if (PyLong_Check(other) && scalar_op) {
		scalar_op(v, PyLong_AsDouble(other), &r_v);
	} else if (PyObject_TypeCheck(other, &py_vec_type) && vector_op) {
		vector_op(v, to_vec_ptr(other), &r_v);
	} else {
		if (scalar_op && vector_op)
			PyErr_SetString(PyExc_RuntimeError, "expected a scalar or Vec instance");
		else if (scalar_op)
			PyErr_SetString(PyExc_RuntimeError, "expected a scalar");
		else
			PyErr_SetString(PyExc_RuntimeError, "expected a Vec instance");
		return NULL;
	}

	if (in_place) {
		memcpy(v, &r_v, sizeof(Vec));
		Py_INCREF(self);
		return self;
	} else {
		PyVecObject *result = PyObject_New(PyVecObject, &py_vec_type);
		memcpy(&result->vec, &r_v, sizeof(Vec));
		return (PyObject*)result;
	}
}

static PyObject*
py_vec_add(PyObject *self, PyObject *other)
{
	return py_vec_op_helper(self, other, vec_addf, vec_addv, 0);
}

static PyObject*
py_vec_iadd(PyObject *self, PyObject *other)
{
	return py_vec_op_helper(self, other, vec_addf, vec_addv, 1);
}

static PyObject*
py_vec_sub(PyObject *self, PyObject *other)
{
	return py_vec_op_helper(self, other, vec_subf, vec_subv, 0);
}

static PyObject*
py_vec_isub(PyObject *self, PyObject *other)
{
	return py_vec_op_helper(self, other, vec_subf, vec_subv, 1);
}

static PyObject*
py_vec_mul(PyObject *self, PyObject *other)
{
	return py_vec_op_helper(self, other, vec_mul, NULL, 0);
}

static PyObject*
py_vec_imul(PyObject *self, PyObject *other)
{
	return py_vec_op_helper(self, other, vec_mul, NULL, 1);
}

static PyObject*
py_vec_neg(PyObject *self)
{
	PyVecObject *result = PyObject_New(PyVecObject, &py_vec_type);
	vec_mul(to_vec_ptr(self), -1, &result->vec);
	return (PyObject*)result;
}

static PyObject*
py_vec_cross(PyObject *self, PyObject *other)
{
	if (!PyObject_TypeCheck(other, &py_vec_type)) {
		PyErr_SetString(PyExc_AttributeError, "expected a Vec instance");
		return NULL;
	}
	Vec *a = to_vec_ptr(self), *b = to_vec_ptr(other);
	PyVecObject *result = PyObject_New(PyVecObject, &py_vec_type);
	vec_cross(a, b, &result->vec);
	return (PyObject*)result;
}

static PyObject*
py_vec_dot(PyObject *self, PyObject *other)
{
	if (!PyObject_TypeCheck(other, &py_vec_type)) {
		PyErr_SetString(PyExc_AttributeError, "expected a Vec instance");
		return NULL;
	}
	Vec *a = to_vec_ptr(self), *b = to_vec_ptr(other);
	return PyFloat_FromDouble(vec_dot(a, b));
}

static PyObject*
py_vec_getter(PyObject *self, void *offset)
{
	Vec *v = to_vec_ptr(self);
	float value = v->data[(size_t)offset];
	return PyFloat_FromDouble(value);
}

static int
py_vec_setter(PyObject *self, PyObject *arg, void *offset)
{
	float value;
	if (PyFloat_Check(arg)) {
		value = PyFloat_AsDouble(arg);
	} else if (PyLong_Check(arg)) {
		value = PyLong_AsDouble(arg);
	} else {
		PyErr_SetString(PyExc_AttributeError, "expected a number");
		return -1;
	}
	Vec *v = to_vec_ptr(self);
	v->data[(size_t)offset] = value;
	return 0;
}

static int
py_vec_getbuffer(PyObject *self, Py_buffer *view, int flags)
{
	return PyBuffer_FillInfo(
		view,
		self,
		(void*)to_vec_ptr(self)->data,
		sizeof(float) * 4,
		0,
		flags
	);
}

#define to_mat(pyobj) (((PyMatObject*)pyobj)->mat)
#define to_mat_ptr(pyobj) (&((PyMatObject*)pyobj)->mat)

static int
py_mat_init(PyObject *self, PyObject *args, PyObject *kwargs);

static PyObject*
py_mat_identity(PyObject *self);

static PyObject*
py_mat_lookat(PyObject *self, PyObject *args);

static PyObject*
py_mat_ortho(PyObject *self, PyObject *args);

static PyObject*
py_mat_persp(PyObject *self, PyObject *args);

static PyObject*
py_mat_repr(PyObject *self);

static PyObject*
py_mat_mul(PyObject *self, PyObject *other);

static PyObject*
py_mat_imul(PyObject *self, PyObject *other);

static PyObject*
py_mat_rotate(PyObject *self, PyObject *args);

static PyObject*
py_mat_scale(PyObject *self, PyObject *svec);

static PyObject*
py_mat_translate(PyObject *self, PyObject *tvec);

static PyObject*
py_mat_invert(PyObject *self);

static PyObject*
py_mat_getitem(PyObject *self, PyObject *key);

static int
py_mat_setitem(PyObject *self, PyObject *key, PyObject *value);

static int
py_mat_getbuffer(PyObject *self, Py_buffer *view, int flags);

static PyObject*
py_mat_cmp(PyObject *self, PyObject *other, int op);

/**
 * Mat method definitions.
 */
static PyMethodDef mat_methods[] = {
	{ "identity", (PyCFunction)py_mat_identity, METH_NOARGS,
	  "Initialize to identity matrix." },
	{ "lookat", (PyCFunction)py_mat_lookat, METH_VARARGS,
	  "Initialize to \"look at\" orientation matrix." },
	{ "ortho", (PyCFunction)py_mat_ortho, METH_VARARGS,
	  "Initialize to orthographic projection matrix." },
	{ "persp", (PyCFunction)py_mat_persp, METH_VARARGS,
	  "Initialize to perspective projection matrix." },
	{ "rotate", (PyCFunction)py_mat_rotate, METH_VARARGS,
	  "Apply a rotation defined by an axis and angle." },
	{ "scale", (PyCFunction)py_mat_scale, METH_O,
	  "Apply a scale defined by X, Y, Z components of given vector." },
	{ "translate", (PyCFunction)py_mat_translate, METH_O,
	  "Apply a translation defined by X, Y, Z components of given vector." },
	{ "invert", (PyCFunction)py_mat_invert, METH_NOARGS,
	  "Invert the matrix." },
	{ NULL }
};

/**
 * Mat mapping methods (for accessing single values)
 */
static PyMappingMethods mat_map_methods = {
	.mp_length = NULL,
	.mp_subscript = py_mat_getitem,
	.mp_ass_subscript = py_mat_setitem
};

/**
 * Mat number protocol methods.
 */
static PyNumberMethods mat_num_methods = {
	.nb_multiply = py_mat_mul,
	.nb_inplace_multiply = py_mat_imul,
};

/**
 * Mat buffer methods.
 */
static PyBufferProcs mat_buf_methods = {
	.bf_getbuffer = py_mat_getbuffer,
	.bf_releasebuffer = NULL
};

/**
 * Mat object type definition.
 */
PyTypeObject py_mat_type = {
	{ PyObject_HEAD_INIT(NULL) },
	.tp_name = "matlib.Mat",
	.tp_doc = "Matrix 4x4.",
	.tp_basicsize = sizeof(PyMatObject),
	.tp_itemsize = 0,
	.tp_alloc = PyType_GenericAlloc,
	.tp_dealloc = NULL,
	.tp_new = PyType_GenericNew,
	.tp_init = py_mat_init,
	.tp_print = NULL,
	.tp_getattr = NULL,
	.tp_setattr = NULL,
	.tp_repr = py_mat_repr,
	.tp_richcompare = py_mat_cmp,
	.tp_as_number = &mat_num_methods,
	.tp_as_sequence = NULL,
	.tp_as_mapping = &mat_map_methods,
	.tp_as_buffer = &mat_buf_methods,
	.tp_as_async = NULL,
	.tp_hash = NULL,
	.tp_call = NULL,
	.tp_str = NULL,
	.tp_getattro = NULL,
	.tp_setattro = NULL,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_methods = mat_methods
};

static int
py_mat_init(PyObject *self, PyObject *args, PyObject *kwargs)
{
	PyObject *r0 = NULL, *r1 = NULL, *r2 = NULL, *r3 = NULL;
	PyObject *other = NULL;
	Mat *m = to_mat_ptr(self);

	if (PyArg_ParseTuple(args, "O", &other) &&
	    PyObject_TypeCheck(other, &py_mat_type)) {
		// build the matrix by copying the one passed as argument
		Mat *other_m = to_mat_ptr(other);
		memcpy(m, other_m, sizeof(Mat));
		return 0;
	}
	PyErr_Clear();

	if (!PyArg_ParseTuple(args, "|(OOOO)", &r0, &r1, &r2, &r3) || (
	    (r0 && r1 && r2 && r3) && (
	    !PyObject_TypeCheck(r0, &py_vec_type) ||
	    !PyObject_TypeCheck(r1, &py_vec_type) ||
	    !PyObject_TypeCheck(r2, &py_vec_type) ||
	    !PyObject_TypeCheck(r3, &py_vec_type)))) {
		PyErr_SetString(
			PyExc_RuntimeError,
			"Mat() expects 4 Vec instances as rows or another Mat instance");
		return -1;
	}

	if (!(r0 && r1 && r2 && r3)) {
		// if no rows are provided, initialize the matrix to identity
		mat_ident(m);
		return 0;
	}

	Vec *vr0 = to_vec_ptr(r0);
	Vec *vr1 = to_vec_ptr(r1);
	Vec *vr2 = to_vec_ptr(r2);
	Vec *vr3 = to_vec_ptr(r3);

	size_t size = sizeof(float) * 4;
	memcpy(m->data, vr0->data, size);
	memcpy(m->data + 4, vr1->data, size);
	memcpy(m->data + 8, vr2->data, size);
	memcpy(m->data + 12, vr3->data, size);

	return 0;
}

static PyObject*
py_mat_identity(PyObject *self)
{
	Mat *m = to_mat_ptr(self);
	mat_ident(m);
	Py_RETURN_NONE;
}

static PyObject*
py_mat_lookat(PyObject *self, PyObject *args)
{
	PyObject *eye = NULL, *center = NULL, *up = NULL;
	if (!PyArg_ParseTuple(args, "OOO", &eye, &center, &up) ||
	    !PyObject_TypeCheck(eye, &py_vec_type) ||
	    !PyObject_TypeCheck(center, &py_vec_type) ||
	    !PyObject_TypeCheck(up, &py_vec_type)) {
			PyErr_SetString(
				PyExc_RuntimeError,
				"expected eye, center and up vectors as Vec instances"
			);
			return NULL;
	}
	Mat *m_self = to_mat_ptr(self);
	Vec *v_eye = to_vec_ptr(eye);
	Vec *v_center = to_vec_ptr(center);
	Vec *v_up = to_vec_ptr(up);
	mat_lookatv(m_self, v_eye, v_center, v_up);
	Py_RETURN_NONE;
}

static PyObject*
py_mat_ortho(PyObject *self, PyObject *args)
{
	float l, r, t, b, n, f;
	if (!PyArg_ParseTuple(args, "ffffff", &l, &r, &t, &b, &n, &f)) {
			PyErr_SetString(
				PyExc_RuntimeError,
				"expected left, right, top, bottom, near, far as floats"
			);
			return NULL;
	}
	Mat *m_self = to_mat_ptr(self);
	mat_ortho(m_self, l, r, t, b, n, f);
	Py_RETURN_NONE;
}

static PyObject*
py_mat_persp(PyObject *self, PyObject *args)
{
	float fovy, aspect, near, far;
	if (!PyArg_ParseTuple(args, "ffff", &fovy, &aspect, &near, &far)) {
			PyErr_SetString(
				PyExc_RuntimeError,
				"expected fovy, aspect, near, far as floats"
			);
			return NULL;
	}
	Mat *m_self = to_mat_ptr(self);
	mat_persp(m_self, fovy, aspect, near, far);
	Py_RETURN_NONE;
}

static PyObject*
py_mat_repr(PyObject *self)
{
	Mat m = to_mat(self);
	char *s = strfmt(
		"Mat(\n"
		"    Vec(%f, %f, %f, %f),\n"
		"    Vec(%f, %f, %f, %f),\n"
		"    Vec(%f, %f, %f, %f),\n"
		"    Vec(%f, %f, %f, %f))\n",
		m.data[0], m.data[1], m.data[2], m.data[3],
		m.data[4], m.data[5], m.data[6], m.data[7],
		m.data[8], m.data[9], m.data[10], m.data[11],
		m.data[12], m.data[13], m.data[14], m.data[15]
	);
	PyObject *repr = PyUnicode_FromString(s);
	free(s);
	return repr;
}

static PyObject*
py_mat_mul_vec(PyObject *self, PyObject *arg)
{
	Mat *mat = to_mat_ptr(self);
	Vec *vec = to_vec_ptr(arg);
	PyVecObject *result = PyObject_New(PyVecObject, &py_vec_type);
	mat_mul_vec(mat, vec, &result->vec);
	return (PyObject*)result;
}

static PyObject*
py_mat_mul(PyObject *self, PyObject *other)
{
	if (PyObject_TypeCheck(other, &py_vec_type)) {
		// matrix - vector multiplication
		return py_mat_mul_vec(self, other);
	}
	if (!PyObject_TypeCheck(other, &py_mat_type)) {
		PyErr_SetString(PyExc_RuntimeError, "expected a Mat instance");
		return NULL;
	}

	Mat *self_mat = to_mat_ptr(self);
	Mat other_mat;
	memcpy(&other_mat, to_mat_ptr(other), sizeof(Mat));
	PyMatObject *result = PyObject_New(PyMatObject, &py_mat_type);
	mat_mul(self_mat, &other_mat, &result->mat);
	return (PyObject*)result;
}

static PyObject*
py_mat_imul(PyObject *self, PyObject *other)
{
	if (!PyObject_TypeCheck(other, &py_mat_type)) {
		PyErr_SetString(PyExc_RuntimeError, "expected a Mat instance");
		return NULL;
	}

	Mat *self_mat = to_mat_ptr(self);
	Mat other_mat;
	memcpy(&other_mat, to_mat_ptr(other), sizeof(Mat));
	Mat tmp;
	mat_mul(self_mat, &other_mat, &tmp);
	memcpy(self_mat, &tmp, sizeof(Mat));

	Py_INCREF(self);
	return (PyObject*)self;
}

static PyObject*
py_mat_rotate(PyObject *self, PyObject *args)
{
	PyObject *axis = NULL;
	float angle = 0;
	if (!PyArg_ParseTuple(args, "Of", &axis, &angle)) {
		PyErr_SetString(PyExc_RuntimeError, "expected a Vec instance and a float");
		return NULL;
	}
	Mat *mat = to_mat_ptr(self);
	Vec *vec = to_vec_ptr(axis);
	mat_rotate(mat, vec, angle);
	Py_RETURN_NONE;
}

static PyObject*
py_mat_scale(PyObject *self, PyObject *svec)
{
	if (!PyObject_TypeCheck(svec, &py_vec_type)) {
		PyErr_SetString(PyExc_RuntimeError, "expected a Vec instance");
		return NULL;
	}
	Mat *mat = to_mat_ptr(self);
	Vec *vec = to_vec_ptr(svec);
	mat_scalev(mat, vec);
	Py_RETURN_NONE;
}

static PyObject*
py_mat_translate(PyObject *self, PyObject *tvec)
{
	if (!PyObject_TypeCheck(tvec, &py_vec_type)) {
		PyErr_SetString(PyExc_RuntimeError, "expected a Vec instance");
		return NULL;
	}
	Mat *mat = to_mat_ptr(self);
	Vec *vec = to_vec_ptr(tvec);
	mat_translatev(mat, vec);
	Py_RETURN_NONE;
}

static PyObject*
py_mat_invert(PyObject *self)
{
	Mat *mat = to_mat_ptr(self);
	Mat tmp;
	mat_invert(mat, &tmp);
	memcpy(mat, &tmp, sizeof(Mat));
	Py_RETURN_NONE;
}

static int
py_mat_parse_indices(PyObject *key, unsigned short *r_i, unsigned short *r_j)
{
	unsigned short i, j;
	if (!PyTuple_Check(key) || !PyArg_ParseTuple(key, "HH", &i, &j)) {
		PyErr_SetString(
			PyExc_KeyError,
			"the key must be an (i,j) tuple of unsigned indices"
		);
		return 0;
	} else if (i > 3 || j > 3) {
		PyErr_SetString(PyExc_KeyError, "indices out of bounds");
		return 0;
	}
	*r_i = i;
	*r_j = j;
	return 1;
}

static PyObject*
py_mat_getitem(PyObject *self, PyObject *key)
{
	unsigned short i, j;
	if (!py_mat_parse_indices(key, &i, &j))
		return NULL;

	Mat mat = to_mat(self);
	return PyFloat_FromDouble(mat.data[i * 4 + j]);
}

static int
py_mat_setitem(PyObject *self, PyObject *key, PyObject *value)
{
	Mat *mat = to_mat_ptr(self);
	unsigned short i, j;
	if (!py_mat_parse_indices(key, &i, &j)) {
		return -1;
	} else if (PyFloat_Check(value)) {
		mat->data[i * 4 + j] = PyFloat_AsDouble(value);
	} else if (PyLong_Check(value)) {
		mat->data[i * 4 + j] = PyLong_AsDouble(value);
	} else {
		PyErr_SetString(PyExc_ValueError, "expected a number");
		return -1;
	}
	return 0;
}

static int
py_mat_getbuffer(PyObject *self, Py_buffer *view, int flags)
{
	return PyBuffer_FillInfo(
		view,
		self,
		(void*)to_mat_ptr(self)->data,
		sizeof(float) * 16,
		0,
		flags
	);
}

static PyObject*
py_mat_cmp(PyObject *self, PyObject *other, int op)
{
	if (!PyObject_TypeCheck(other, &py_mat_type)) {
		if (op == Py_NE) {
			Py_RETURN_TRUE;
		} else if (op == Py_EQ) {
			Py_RETURN_FALSE;
		} else {
			PyErr_SetString(PyExc_TypeError, "unsupported comparison");
			return NULL;
		}
	}
	Mat *m_self = to_mat_ptr(self);
	Mat *m_other = to_mat_ptr(other);
	int equal = memcmp(m_self->data, m_other->data, sizeof(float) * 16) == 0;
	int retval = op == Py_EQ ? equal : !equal;
	if (retval)
		Py_RETURN_TRUE;
	Py_RETURN_FALSE;
}

int
register_matlib(PyObject *parent)
{
	PyObject *matlib = PyModule_Create(&matlib_module);
	if (!matlib) {
		fprintf(stderr, "failed to initialize matlib module\n");
		return 0;
	}

	// add Vec type
	if (PyType_Ready(&py_vec_type) < 0 || PyModule_AddObject(matlib, "Vec", (PyObject*)&py_vec_type) < 0)
		raise_pyerror();

	// add Mat type
	if (PyType_Ready(&py_mat_type) < 0 || PyModule_AddObject(matlib, "Mat", (PyObject*)&py_mat_type) < 0)
		raise_pyerror();

	PyModule_AddObject(parent, "matlib", matlib);

	return 1;
}
