#include <Python.h>  // must be first

#include "matlib.h"
#ifdef __APPLE__
# include <Accelerate/Accelerate.h>
#else
# include <cblas.h>
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
	mat_ident(m);
	m->data[0] = sx;
	m->data[5] = sy;
	m->data[10] = sz;
}

void
mat_scalev(Mat *m, const Vec *sv)
{
	mat_scale(m, sv->data[0], sv->data[1], sv->data[2]);
}

void
mat_translate(Mat *m, float tx, float ty, float tz)
{
	mat_ident(m);
	m->data[3] = tx;
	m->data[7] = ty;
	m->data[11] = tz;
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
mat_inv(Mat *m, Mat *out_m)
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
vec_mul(Vec *v, float scalar, Vec *r_v)
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
vec_len(const Vec *v)
{
	float x = v->data[0], y = v->data[1], z = v->data[2], w = v->data[3];
	return sqrt(x * x + y * y + z * z + w * w);
}

void
vec_norm(Vec *v)
{
	vec_mul(v, 1.0f / vec_len(v), v);
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
py_vec_add(PyObject *self, PyObject *args);

static PyObject*
py_vec_mul(PyObject *self, PyObject *args);

static PyObject*
py_vec_cross(PyObject *unused, PyObject *args);

static PyObject*
py_vec_dot(PyObject *unused, PyObject *args);

/**
 * Vec class methods.
 */
static PyMethodDef vec_methods[] = {
	{ "norm", (PyCFunction)py_vec_norm, METH_NOARGS,
	  "Normalize the vector." },
	{ "add", (PyCFunction)py_vec_add, METH_VARARGS,
	  "Add a scalar or another vector." },
	{ "mul", (PyCFunction)py_vec_mul, METH_VARARGS,
	  "Multiply by a scalar." },
	{ "cross", (PyCFunction)py_vec_cross, METH_VARARGS | METH_STATIC,
	  "Perform cross product between two vectors." },
	{ "dot", (PyCFunction)py_vec_dot, METH_VARARGS | METH_STATIC,
	  "Perform dot product between two vectors." },
	{ NULL }
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
	.tp_methods = vec_methods
};

static PyObject*
py_vec_repr(PyObject *self)
{
	Vec v = to_vec(self);
	PyObject *x = PyFloat_FromDouble(v.data[0]);
	PyObject *y = PyFloat_FromDouble(v.data[1]);
	PyObject *z = PyFloat_FromDouble(v.data[2]);
	PyObject *w = PyFloat_FromDouble(v.data[3]);
	PyObject *repr = PyUnicode_FromFormat("Vec(%A, %A, %A, %A)", x, y, z, w);
	Py_DECREF(x);
	Py_DECREF(y);
	Py_DECREF(z);
	Py_DECREF(w);
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
py_vec_add(PyObject *self, PyObject *args)
{
	float scalar = 0.0;
	Vec *v = to_vec_ptr(self);
	PyObject *o = NULL;

	if (PyArg_ParseTuple(args, "f", &scalar)) {
		// add the scalar to each component
		vec_addf(v, scalar, v);
		Py_RETURN_NONE;
	} else if (PyArg_ParseTuple(args, "O", &o)) {
		// discard the error generated by previous PyArg_ParseTuple() call
		PyErr_Clear();

		if (PyObject_TypeCheck(o, &py_vec_type)) {
			// add other vector's components to self
			Vec *other = to_vec_ptr(o);
			vec_addv(v, other, v);
			Py_RETURN_NONE;
		}
	}
	PyErr_SetString(PyExc_RuntimeError, "expected a scalar or Vec instance");
	return NULL;
}

static PyObject*
py_vec_mul(PyObject *self, PyObject *args)
{
	float scalar = 0.0;
	Vec *v = to_vec_ptr(self);
	if (!PyArg_ParseTuple(args, "f", &scalar)) {
		PyErr_SetString(PyExc_RuntimeError, "expected a scalar");
		return NULL;
	}
	vec_mul(v, scalar, v);
	Py_RETURN_NONE;
}

static int
get_vec_args(PyObject *args, Vec **r_a, Vec **r_b)
{
	PyObject *a = NULL, *b = NULL;
	if (!PyArg_ParseTuple(args, "OO", &a, &b) ||
	    !PyObject_TypeCheck(a, &py_vec_type) ||
	    !PyObject_TypeCheck(b, &py_vec_type)) {
		PyErr_SetString(PyExc_RuntimeError, "expected two Vec instances");
		return 0;
	}
	*r_a = to_vec_ptr(a);
	*r_b = to_vec_ptr(b);
	return 1;
}

static PyObject*
py_vec_cross(PyObject *unused, PyObject *args)
{
	Vec *a = NULL, *b = NULL;
	if (!get_vec_args(args, &a, &b))
		return NULL;

	PyVecObject *result = PyObject_New(PyVecObject, &py_vec_type);
	vec_cross(a, b, &result->vec);
	return (PyObject*)result;
}

static PyObject*
py_vec_dot(PyObject *unused, PyObject *args)
{
	Vec *a = NULL, *b = NULL;
	if (!get_vec_args(args, &a, &b))
		return NULL;
	return PyFloat_FromDouble(vec_dot(a, b));
}

static void
raise_pyerror(void)
{
	fprintf(stderr, "Python error occurred\n");
	exit(EXIT_FAILURE);
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

	return m;
}
