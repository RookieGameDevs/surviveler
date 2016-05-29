#include <Python.h>  // must be first

#include "matlib.h"
#ifdef __APPLE__
# include <Accelerate/Accelerate.h>
#else
# include <cblas.h>
#endif

void
mat4_mul(const Mat4 *a, const Mat4 *b, Mat4 *r)
{
	memset(r, 0, sizeof(Mat4));
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
mat4_mul_vec(const Mat4 *m, const Vec4 *v, Vec4 *r_v)
{
	memset(r_v, 0, sizeof(Vec4));
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
mat4_rotate(Mat4 *m, const Vec3 *v, float angle)
{
	const float x = v->data[0];
	const float y = v->data[1];
	const float z = v->data[2];
	const float sin_a = sin(angle);
	const float cos_a = cos(angle);
	const float k = 1 - cos(angle);

	memset(m, 0, sizeof(Mat4));
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
mat4_scale(Mat4 *m, float sx, float sy, float sz)
{
	mat4_ident(m);
	m->data[0] = sx;
	m->data[5] = sy;
	m->data[10] = sz;
}

void
mat4_scalev(Mat4 *m, const Vec3 *sv)
{
	mat4_scale(m, sv->data[0], sv->data[1], sv->data[2]);
}

void
mat4_translate(Mat4 *m, float tx, float ty, float tz)
{
	mat4_ident(m);
	m->data[3] = tx;
	m->data[7] = ty;
	m->data[11] = tz;
}

void
mat4_translatev(Mat4 *m, const Vec3 *tv)
{
	mat4_translate(m, tv->data[0], tv->data[1], tv->data[2]);
}

void
mat4_ident(Mat4 *m)
{
	memset(m, 0, sizeof(Mat4));
	m->data[0] = m->data[5] = m->data[10] = m->data[15] = 1;
}

int
mat4_inv(Mat4 *m, Mat4 *out_m)
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

Vec3
vec3(float x, float y, float z)
{
	Vec3 v = {{ x, y, z }};
	return v;
}

void
vec3_sum(const Vec3 *a, const Vec3 *b, Vec3 *r_v)
{
	for (short i = 0; i < 3; i++) {
		r_v->data[i] = a->data[i] + b->data[i];
	}
}

void
vec3_mul(Vec3 *v, float scalar)
{
	for (short i = 0; i < 3; i++) {
		v->data[i] *= scalar;
	}
}

float
vec3_len(const Vec3 *v)
{
	float x = v->data[0], y = v->data[1], z = v->data[2];
	return sqrt(x * x + y * y + z * z);
}

void
vec3_norm(Vec3 *v)
{
	vec3_mul(v, 1.0f / vec3_len(v));
}


float
vec3_dot(const Vec3 *a, const Vec3 *b)
{
	return cblas_sdot(3, a->data, 1, b->data, 1);

}

void
vec3_cross(const Vec3 *a, const Vec3 *b, Vec3 *r_v)
{
	r_v->data[0] = a->data[1] * b->data[2] - a->data[2] * b->data[1];
	r_v->data[1] = a->data[2] * b->data[0] - a->data[0] * b->data[2];
	r_v->data[2] = a->data[0] * b->data[1] - a->data[1] * b->data[0];
}

Vec4
vec4(float x, float y, float z, float w)
{
	Vec4 v = {{ x, y, z, w }};
	return v;
}

void
vec4_sum(const Vec4 *a, const Vec4 *b, Vec4 *r_v)
{
	for (short i = 0; i < 4; i++) {
		r_v->data[i] = a->data[i] + b->data[i];
	}
}

void
vec4_mul(Vec4 *v, float scalar)
{
	for (short i = 0; i < 4; i++) {
		v->data[i] *= scalar;
	}
}

float
vec4_len(const Vec4 *v)
{
	float x = v->data[0], y = v->data[1], z = v->data[2], w = v->data[3];
	return sqrt(x * x + y * y + z * z + w * w);
}

void
vec4_norm(Vec4 *v)
{
	vec4_mul(v, 1.0f / vec4_len(v));
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
 * Vec4 type wrapper.
 */
typedef struct _PyVecObject {
	PyObject_HEAD
	Vec4 vec;
} PyVecObject;

#define to_vec4(pyobj) (((PyVecObject*)pyobj)->vec)
#define to_vec4_ptr(pyobj) (&((PyVecObject*)pyobj)->vec)

static PyObject*
py_vec_repr(PyObject *self)
{
	Vec4 v = to_vec4(self);
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
	double x, y, z, w;
	if (!PyArg_ParseTuple(args, "|dddd", &x, &y, &z, &w)) {
		PyErr_SetString(PyExc_RuntimeError, "expected at most 4 floats");
		return -1;
	}

	float data[] = { x, y, z, w };
	memcpy(to_vec4(self).data, data, sizeof(float) * 4);
	return 0;
}

static PyObject*
py_vec_norm(PyObject *self)
{
	vec4_norm(to_vec4_ptr(self));
	Py_RETURN_NONE;
}

static PyObject*
py_vec_add(PyObject *self, PyObject *other)
{
	// TODO
	return NULL;
}

static PyObject*
py_vec_mul(PyObject *self, PyObject *other)
{
	// TODO
	return NULL;
}

static PyObject*
py_vec_cross(PyObject *self, PyObject *other)
{
	// TODO
	return NULL;
}

static PyMethodDef vec_methods[] = {
	{ "norm", (PyCFunction)py_vec_norm, METH_VARARGS,
	  "Normalize the vector." },
	{ "add", (PyCFunction)py_vec_add, 0,
	  "Add a scalar or another vector." },
	{ "mul", (PyCFunction)py_vec_mul, 0,
	  "Multiply by a scalar, another vector (dot product) or matrix." },
	{ "cross", (PyCFunction)py_vec_cross, 0,
	  "Perform cross product with another vector." },
	{ NULL }
};

/**
 * Vec4 object type definition.
 */
static PyTypeObject vec4_type = {
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

	// add Vec4 type
	if (PyType_Ready(&vec4_type) < 0 || PyModule_AddObject(m, "Vec", (PyObject*)&vec4_type) < 0)
		raise_pyerror();

	return m;
}
