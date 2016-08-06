#include "matlib.h"
#include <string.h>
#include <stdarg.h>

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
	Mat rm, tmp;
	mat_ident(&rm);

	const float x = v->data[0];
	const float y = v->data[1];
	const float z = v->data[2];
	const float sin_a = sin(angle);
	const float cos_a = cos(angle);
	const float k = 1 - cos(angle);

	rm.data[0] = cos_a + k * x * x;
	rm.data[1] = k * x * y - z * sin_a;
	rm.data[2] = k * x * z + y * sin_a;
	rm.data[4] = k * x * y + z * sin_a;
	rm.data[5] = cos_a + k * y * y;
	rm.data[6] = k * y * z - x * sin_a;
	rm.data[8] = k * x * z - y * sin_a;
	rm.data[9] = k * y * z + x * sin_a;
	rm.data[10] = cos_a + k * z * z;
	rm.data[15] = 1.0f;

	mat_mul(m, &rm, &tmp);
	memcpy(m, &tmp, sizeof(Mat));
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

Mat
mat_from_qtr(const Qtr *q)
{
	float w = q->data[0], x = q->data[1], y = q->data[2], z = q->data[3];
	Mat m = {{
		1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w),       2.0 * (x * z + y * w),       0.0,
		2.0 * (x * y + z * w),       1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w),       0.0,
		2.0 * (x * z - y * w),       2.0 * (y * z + x * w),       1.0 - 2.0 * (x * x + y * y), 0.0,
		0.0,                         0.0,                         0.0,                         1.0
	}};
	return m;
}

void
mat_lookat(
	Mat *m,
	float eye_x, float eye_y, float eye_z,
	float center_x, float center_y, float center_z,
	float up_x, float up_y, float up_z
) {
	Vec eye = vec(eye_x, eye_y, eye_z, 0);
	Vec center = vec(center_x, center_y, center_z, 0);
	Vec up = vec(up_x, up_y, up_z, 0);
	mat_lookatv(m, &eye, &center, &up);
}

void
mat_lookatv(Mat *m, const Vec *eye, const Vec *center, const Vec *up)
{
	Vec z;
	vec_subv(center, eye, &z);
	vec_norm(&z);

	Vec up_norm;
	memcpy(&up_norm, up, sizeof(Vec));
	vec_norm(&up_norm);

	Vec x;
	vec_cross(&z, &up_norm, &x);
	vec_norm(&x);

	Vec y;
	vec_cross(&x, &z, &y);
	vec_norm(&y);

	Mat lookat = {{
		 x.data[0],  x.data[1],  x.data[2], 0.0,
		 y.data[0],  y.data[1],  y.data[2], 0.0,
		-z.data[0], -z.data[1], -z.data[2], 0.0,
		0,          0,          0,          1
	}};
	mat_translate(&lookat, -eye->data[0], -eye->data[1], -eye->data[2]);
	memcpy(m, &lookat, sizeof(Mat));
}

void
mat_ortho(Mat *m, float l, float r, float t, float b, float n, float f)
{
	float x = 2.0f / (r - l);
	float y = 2.0f / (t - b);
	float z = -2.0f / (f - n);

	float tx = -(r + l) / (r - l);
	float ty = -(t + b) / (t - b);
	float tz = -(f + n) / (f - n);

	Mat ortho = {{
		x, 0, 0, tx,
		0, y, 0, ty,
		0, 0, z, tz,
		0, 0, 0, 1
	}};
	memcpy(m, &ortho, sizeof(Mat));
}

void
mat_persp(Mat *m, float fovy, float aspect, float n, float f)
{
	fovy = M_PI / 180.0 * fovy;
	float y = 1.0 / (fovy / 2.0);
	float x = y / aspect;
	float z = (f + n) / (n - f);
	float tz = (2 * f * n) / (n - f);
	Mat persp = {{
		x, 0, 0, 0,
		0, y, 0, 0,
		0, 0, z, tz,
		0, 0, -1, 0
	}};
	memcpy(m, &persp, sizeof(Mat));
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
	return cblas_sdot(3, a->data, 1, b->data, 1);
}

float
vec_mag(const Vec *v)
{
	float x = v->data[0], y = v->data[1], z = v->data[2];
	return sqrt(x * x + y * y + z * z);
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

void
vec_lerp(const Vec *a, const Vec *b, float t, Vec *r_v)
{
	Vec at, bt;
	vec_mul(a, 1 - t, &at);
	vec_mul(b, t, &bt);
	vec_addv(&at, &bt, r_v);
}


Qtr
qtr(float w, float x, float y, float z)
{
	Qtr q = {{w, x, y, z}};
	return q;
}

Qtr
qtr_rotation(float x, float y, float z, float angle)
{
	float s = sin(angle / 2.0f);
	Qtr q = {{
		cos(angle / 2.0f),
		x * s,
		y * s,
		z * s,
	}};
	return q;
}

void
qtr_mulf(const Qtr *a, float scalar, Qtr *r_q)
{
	r_q->data[0] = a->data[0] * scalar;
	r_q->data[1] = a->data[1] * scalar;
	r_q->data[2] = a->data[2] * scalar;
	r_q->data[3] = a->data[3] * scalar;
}

void
qtr_mul(const Qtr *a, const Qtr *b, Qtr *r_q)
{
	r_q->data[1] =  a->data[1] * b->data[0] + a->data[2] * b->data[3] - a->data[3] * b->data[2] + a->data[0] * b->data[1];
	r_q->data[2] = -a->data[1] * b->data[3] + a->data[2] * b->data[0] + a->data[3] * b->data[1] + a->data[0] * b->data[2];
	r_q->data[3] =  a->data[1] * b->data[2] - a->data[2] * b->data[1] + a->data[3] * b->data[0] + a->data[0] * b->data[3];
	r_q->data[0] = -a->data[1] * b->data[1] - a->data[2] * b->data[2] - a->data[3] * b->data[3] + a->data[0] * b->data[0];
}

void
qtr_add(const Qtr *a, const Qtr *b, Qtr *r_q)
{
	r_q->data[0] = a->data[0] + b->data[0];
	r_q->data[1] = a->data[1] + b->data[1];
	r_q->data[2] = a->data[2] + b->data[2];
	r_q->data[3] = a->data[3] + b->data[3];
}

void
qtr_norm(Qtr *q)
{
	float n = sqrt(
		q->data[0] * q->data[0] +
		q->data[1] * q->data[1] +
		q->data[2] * q->data[2] +
		q->data[3] * q->data[3]
	);
	q->data[0] /= n;
	q->data[1] /= n;
	q->data[2] /= n;
	q->data[3] /= n;
}

void
qtr_lerp(const Qtr *a, const Qtr *b, float t, Qtr *r_q)
{
	Qtr at, bt;
	qtr_mulf(a, 1 - t, &at);
	qtr_mulf(b, t, &bt);
	qtr_add(&at, &bt, r_q);
	qtr_norm(r_q);
}
