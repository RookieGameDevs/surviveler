#include <Python.h>  // must be first

#include "matlib.h"
#include <stdarg.h>

#ifdef __APPLE__
# include <Accelerate/Accelerate.h>
#else
# include <cblas.h>
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

void
mat_mul(const Mat *a, const Mat *b, Mat *r)
{
	memset(r, 0, sizeof(Mat));
	cblas_sgemm(
		CblasRowMajor,  // row-major order
		CblasNoTrans,   // don't transpose the first matrix
		CblasNoTrans,   // ... neither the second
		4, 4, 4,        // M, N, K sizes
		1,              // scalar to multiply first
		a->data,        // first matrix
		4,              // stride of the first matrix
		b->data,        // second matrix
		4,              // stride
		1,              // scalar to multiply the result by
		r->data,        // result matrix pointer
		4               // stride of result matrix
	);
}

void
mat_mul_vec(const Mat *m, const Vec *v, Vec *r_v)
{
	memset(r_v, 0, sizeof(Vec));
	cblas_sgemv(
		CblasRowMajor,  // row-major order
		CblasNoTrans,   // do not transpose the matrix
		4, 4,           // M and N dimensions
		1,              // scalar to premultiply
		m->data,        // matrix data
		4,              // matrix stride
		v->data,        // vector data
		1,              // vector inter-element increment
		1,              // scalar to postmultiply
		r_v->data,      // result buffer
		1               // result buffer inter-element increment
	);
}

void
mat_rotate(Mat *m, const Vec *v, float angle)
{
	const float x = v->data[0];
	const float y = v->data[1];
	const float z = v->data[2];
	const float sin_a = sin(angle);
	const float cos_a = cos(angle);
	const float k = 1 - cos(angle);

	memset(m, 0, sizeof(Mat));
	float *md = m->data;
	md[0] = cos_a + k * x * x;
	md[1] = k * x * y - z * sin_a;
	md[2] = k * x * z + y * sin_a;

	md[4] = k * x * y + z * sin_a;
	md[5] = cos_a + k * y * y;
	md[6] = k * y * z - x * sin_a;

	md[8] = k * x * z - y * sin_a;
	md[9] = k * y * z + x * sin_a;
	md[10] = cos_a + k * z * z;

	md[15] = 1.0f;
}

void
mat_scale(Mat *m, float sx, float sy, float sz)
{
	Mat sm, tmp;
	mat_ident(&sm);
	sm.data[0] = sx;
	sm.data[5] = sy;
	sm.data[10] = sz;
	mat_mul(m, &sm, &tmp);
	memcpy(m, &tmp, sizeof(Mat));
}

void
mat_scalev(Mat *m, const Vec *sv)
{
	mat_scale(m, sv->data[0], sv->data[1], sv->data[2]);
}

void
mat_translate(Mat *m, float tx, float ty, float tz)
{
	Mat tm, tmp;
	mat_ident(&tm);
	tm.data[3] = tx;
	tm.data[7] = ty;
	tm.data[11] = tz;
	mat_mul(m, &tm, &tmp);
	memcpy(m, &tmp, sizeof(Mat));
}

void
mat_translatev(Mat *m, const Vec *tv)
{
	mat_translate(m, tv->data[0], tv->data[1], tv->data[2]);
}

void
mat_ident(Mat *m)
{
	memset(m, 0, sizeof(Mat));
	m->data[0] = m->data[5] = m->data[10] = m->data[15] = 1;
}

int
mat_invert(Mat *m, Mat *out_m)
{
	float inv[16], det;
	float *mdata = m->data;
	float *out_mdata = out_m->data;

	inv[0] = mdata[5]  * mdata[10] * mdata[15] -
	         mdata[5]  * mdata[11] * mdata[14] -
	         mdata[9]  * mdata[6]  * mdata[15] +
	         mdata[9]  * mdata[7]  * mdata[14] +
	         mdata[13] * mdata[6]  * mdata[11] -
	         mdata[13] * mdata[7]  * mdata[10];

	inv[4] = -mdata[4]  * mdata[10] * mdata[15] +
	         mdata[4]  * mdata[11] * mdata[14] +
	         mdata[8]  * mdata[6]  * mdata[15] -
	         mdata[8]  * mdata[7]  * mdata[14] -
	         mdata[12] * mdata[6]  * mdata[11] +
	         mdata[12] * mdata[7]  * mdata[10];

	inv[8] = mdata[4]  * mdata[9] * mdata[15] -
	         mdata[4]  * mdata[11] * mdata[13] -
	         mdata[8]  * mdata[5] * mdata[15] +
	         mdata[8]  * mdata[7] * mdata[13] +
	         mdata[12] * mdata[5] * mdata[11] -
	         mdata[12] * mdata[7] * mdata[9];

	inv[12] = -mdata[4]  * mdata[9] * mdata[14] +
	         mdata[4]  * mdata[10] * mdata[13] +
	         mdata[8]  * mdata[5] * mdata[14] -
	         mdata[8]  * mdata[6] * mdata[13] -
	         mdata[12] * mdata[5] * mdata[10] +
	         mdata[12] * mdata[6] * mdata[9];

	inv[1] = -mdata[1]  * mdata[10] * mdata[15] +
	         mdata[1]  * mdata[11] * mdata[14] +
	         mdata[9]  * mdata[2] * mdata[15] -
	         mdata[9]  * mdata[3] * mdata[14] -
	         mdata[13] * mdata[2] * mdata[11] +
	         mdata[13] * mdata[3] * mdata[10];

	inv[5] = mdata[0]  * mdata[10] * mdata[15] -
	         mdata[0]  * mdata[11] * mdata[14] -
	         mdata[8]  * mdata[2] * mdata[15] +
	         mdata[8]  * mdata[3] * mdata[14] +
	         mdata[12] * mdata[2] * mdata[11] -
	         mdata[12] * mdata[3] * mdata[10];

	inv[9] = -mdata[0]  * mdata[9] * mdata[15] +
	         mdata[0]  * mdata[11] * mdata[13] +
	         mdata[8]  * mdata[1] * mdata[15] -
	         mdata[8]  * mdata[3] * mdata[13] -
	         mdata[12] * mdata[1] * mdata[11] +
	         mdata[12] * mdata[3] * mdata[9];

	inv[13] = mdata[0]  * mdata[9] * mdata[14] -
	          mdata[0]  * mdata[10] * mdata[13] -
	          mdata[8]  * mdata[1] * mdata[14] +
	          mdata[8]  * mdata[2] * mdata[13] +
	          mdata[12] * mdata[1] * mdata[10] -
	          mdata[12] * mdata[2] * mdata[9];

	inv[2] = mdata[1]  * mdata[6] * mdata[15] -
	         mdata[1]  * mdata[7] * mdata[14] -
	         mdata[5]  * mdata[2] * mdata[15] +
	         mdata[5]  * mdata[3] * mdata[14] +
	         mdata[13] * mdata[2] * mdata[7] -
	         mdata[13] * mdata[3] * mdata[6];

	inv[6] = -mdata[0]  * mdata[6] * mdata[15] +
	         mdata[0]  * mdata[7] * mdata[14] +
	         mdata[4]  * mdata[2] * mdata[15] -
	         mdata[4]  * mdata[3] * mdata[14] -
	         mdata[12] * mdata[2] * mdata[7] +
	         mdata[12] * mdata[3] * mdata[6];

	inv[10] = mdata[0]  * mdata[5] * mdata[15] -
	          mdata[0]  * mdata[7] * mdata[13] -
	          mdata[4]  * mdata[1] * mdata[15] +
	          mdata[4]  * mdata[3] * mdata[13] +
	          mdata[12] * mdata[1] * mdata[7] -
	          mdata[12] * mdata[3] * mdata[5];

	inv[14] = -mdata[0]  * mdata[5] * mdata[14] +
	          mdata[0]  * mdata[6] * mdata[13] +
	          mdata[4]  * mdata[1] * mdata[14] -
	          mdata[4]  * mdata[2] * mdata[13] -
	          mdata[12] * mdata[1] * mdata[6] +
	          mdata[12] * mdata[2] * mdata[5];

	inv[3] = -mdata[1] * mdata[6] * mdata[11] +
	         mdata[1] * mdata[7] * mdata[10] +
	         mdata[5] * mdata[2] * mdata[11] -
	         mdata[5] * mdata[3] * mdata[10] -
	         mdata[9] * mdata[2] * mdata[7] +
	         mdata[9] * mdata[3] * mdata[6];

	inv[7] = mdata[0] * mdata[6] * mdata[11] -
	         mdata[0] * mdata[7] * mdata[10] -
	         mdata[4] * mdata[2] * mdata[11] +
	         mdata[4] * mdata[3] * mdata[10] +
	         mdata[8] * mdata[2] * mdata[7] -
	         mdata[8] * mdata[3] * mdata[6];

	inv[11] = -mdata[0] * mdata[5] * mdata[11] +
	          mdata[0] * mdata[7] * mdata[9] +
	          mdata[4] * mdata[1] * mdata[11] -
	          mdata[4] * mdata[3] * mdata[9] -
	          mdata[8] * mdata[1] * mdata[7] +
	          mdata[8] * mdata[3] * mdata[5];

	inv[15] = mdata[0] * mdata[5] * mdata[10] -
	          mdata[0] * mdata[6] * mdata[9] -
		  mdata[4] * mdata[1] * mdata[10] +
		  mdata[4] * mdata[2] * mdata[9] +
		  mdata[8] * mdata[1] * mdata[6] -
		  mdata[8] * mdata[2] * mdata[5];

	det = mdata[0] * inv[0] + mdata[1] * inv[4] +
	      mdata[2] * inv[8] + mdata[3] * inv[12];
	if (det == 0)
		return 0;

	det = 1.0 / det;

	for (int i = 0; i < 16; i++)
		out_mdata[i] = inv[i] * det;

	return 1;
}

Vec
vec(float x, float y, float z, float w)
{
	Vec v = {{ x, y, z, w }};
	return v;
}

void
vec_addf(const Vec *a, float scalar, Vec *r_v)
{
	r_v->data[0] = a->data[0] + scalar;
	r_v->data[1] = a->data[1] + scalar;
	r_v->data[2] = a->data[2] + scalar;
	r_v->data[3] = a->data[3] + scalar;
}

void
vec_addv(const Vec *a, const Vec *b, Vec *r_v)
{
	r_v->data[0] = a->data[0] + b->data[0];
	r_v->data[1] = a->data[1] + b->data[1];
	r_v->data[2] = a->data[2] + b->data[2];
	r_v->data[3] = a->data[3] + b->data[3];
}

void
vec_subf(const Vec *a, float scalar, Vec *r_v)
{
	r_v->data[0] = a->data[0] - scalar;
	r_v->data[1] = a->data[1] - scalar;
	r_v->data[2] = a->data[2] - scalar;
	r_v->data[3] = a->data[3] - scalar;
}

void
vec_subv(const Vec *a, const Vec *b, Vec *r_v)
{
	r_v->data[0] = a->data[0] - b->data[0];
	r_v->data[1] = a->data[1] - b->data[1];
	r_v->data[2] = a->data[2] - b->data[2];
	r_v->data[3] = a->data[3] - b->data[3];
}

void
vec_mul(const Vec *v, float scalar, Vec *r_v)
{
	r_v->data[0] = v->data[0] * scalar;
	r_v->data[1] = v->data[1] * scalar;
	r_v->data[2] = v->data[2] * scalar;
	r_v->data[3] = v->data[3] * scalar;
}

float
vec_dot(const Vec *a, const Vec *b)
{
	return cblas_sdot(4, a->data, 1, b->data, 1);
}

float
vec_mag(const Vec *v)
{
	float x = v->data[0], y = v->data[1], z = v->data[2], w = v->data[3];
	return sqrt(x * x + y * y + z * z + w * w);
}

void
vec_norm(Vec *v)
{
	vec_mul(v, 1.0f / vec_mag(v), v);
}

void
vec_cross(const Vec *a, const Vec *b, Vec *r_v)
{
	r_v->data[0] = a->data[1] * b->data[2] - a->data[2] * b->data[1];
	r_v->data[1] = a->data[2] * b->data[0] - a->data[0] * b->data[2];
	r_v->data[2] = a->data[0] * b->data[1] - a->data[1] * b->data[0];
	r_v->data[3] = 0;  // no cross product exists for 4D vectors
}

/******************************************************************************
 *  Utility functions
 *****************************************************************************/
char*
strfmt(const char *fmt, ...)
{
	va_list ap, ap_copy;
	va_start(ap, fmt);

	va_copy(ap_copy, ap);
	size_t msg_len = vsnprintf(NULL, 0, fmt, ap_copy) + 1;
	va_end(ap_copy);

	char *msg = malloc(msg_len);
	if (msg) {
		va_copy(ap_copy, ap);
		vsnprintf(msg, msg_len, fmt, ap_copy);
		va_end(ap_copy);
	}
	va_end(ap);
	return msg;
}

/******************************************************************************
 * Python3 wrappers.
 *****************************************************************************/

/**
 * Module definition.
 */
static struct PyModuleDef module = {
	PyModuleDef_HEAD_INIT,
	"matlib",
	NULL,
	-1,
	NULL
};

/**
 * Vec type wrapper.
 */
typedef struct _PyVecObject {
	PyObject_HEAD
	Vec vec;
} PyVecObject;

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
	  "Get vector's magnitude (length)." },
	{ "cross", (PyCFunction)py_vec_cross, METH_O,
	  "Perform cross product between two vectors." },
	{ "dot", (PyCFunction)py_vec_dot, METH_O,
	  "Perform dot product between two vectors." },
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
static PyTypeObject py_vec_type = {
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
		1,
		flags
	);
}

static void
raise_pyerror(void)
{
	fprintf(stderr, "Python error occurred\n");
	exit(EXIT_FAILURE);
}

/**
 * Mat type wrapper.
 */
typedef struct _PyMatObject {
	PyObject_HEAD
	Mat mat;
} PyMatObject;

#define to_mat(pyobj) (((PyMatObject*)pyobj)->mat)
#define to_mat_ptr(pyobj) (&((PyMatObject*)pyobj)->mat)

static int
py_mat_init(PyObject *self, PyObject *args, PyObject *kwargs);

static PyObject*
py_mat_identity(void);

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

/**
 * Mat method definitions.
 */
static PyMethodDef mat_methods[] = {
	{ "identity", (PyCFunction)py_mat_identity, METH_NOARGS | METH_STATIC,
	  "Create an identity matrix." },
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
 * Mat object type definition.
 */
static PyTypeObject py_mat_type = {
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
	.tp_as_number = &mat_num_methods,
	.tp_as_sequence = NULL,
	.tp_as_mapping = &mat_map_methods,
	.tp_as_buffer = NULL,
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
	if (!PyArg_ParseTuple(args, "OOOO", &r0, &r1, &r2, &r3) ||
	    !PyObject_TypeCheck(r0, &py_vec_type) ||
	    !PyObject_TypeCheck(r1, &py_vec_type) ||
	    !PyObject_TypeCheck(r2, &py_vec_type) ||
	    !PyObject_TypeCheck(r3, &py_vec_type)) {
		PyErr_SetString(
			PyExc_RuntimeError,
			"Mat() expects 4 Vec instances as rows");
		return -1;
	}

	Mat *m = to_mat_ptr(self);
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
py_mat_identity(void)
{
	PyMatObject *mo = PyObject_New(PyMatObject, &py_mat_type);
	if (mo) {
		mat_ident(&mo->mat);
		return (PyObject*)mo;
	}
	return NULL;
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
	unsigned short i, j;
	if (!py_mat_parse_indices(key, &i, &j)) {
		return -1;
	} else if (!PyFloat_Check(value)) {
		PyErr_SetString(PyExc_ValueError, "expected a float");
		return 0;
	}

	Mat *mat = to_mat_ptr(self);
	mat->data[i * 4 + j] = PyFloat_AsDouble(value);
	return 0;
}

/**
 * Module initialization function.
 */
PyMODINIT_FUNC
PyInit_matlib(void)
{

	PyObject *m = PyModule_Create(&module);
	if (!m)
		raise_pyerror();

	// add Vec type
	if (PyType_Ready(&py_vec_type) < 0 || PyModule_AddObject(m, "Vec", (PyObject*)&py_vec_type) < 0)
		raise_pyerror();

	// add Mat type
	if (PyType_Ready(&py_mat_type) < 0 || PyModule_AddObject(m, "Mat", (PyObject*)&py_mat_type) < 0)
		raise_pyerror();

	return m;
}
