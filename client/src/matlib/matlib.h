#pragma once

#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif


typedef struct Mat4 {
	float data[16];
} Mat4;

typedef struct Vec {
	float data[4];
} Vec;

void
mat4_mul(const Mat4 *a, const Mat4 *b, Mat4 *r_m);

void
mat4_mul_vec(const Mat4 *m, const Vec *v, Vec *r_v);

void
mat4_rotate(Mat4 *m, const Vec *v, float angle);

void
mat4_scale(Mat4 *m, float sx, float sy, float sz);

void
mat4_scalev(Mat4 *m, const Vec *sv);

void
mat4_translate(Mat4 *m, float tx, float ty, float tz);

void
mat4_translatev(Mat4 *m, const Vec *tv);

void
mat4_ident(Mat4 *m);

int
mat4_inv(Mat4 *m, Mat4 *out_m);

void
mat4_print(const Mat4 *m);

Vec
vec(float x, float y, float z, float w);

void
vec_addf(const Vec *a, float scalar, Vec *r_v);

void
vec_addv(const Vec *a, const Vec *b, Vec *r_v);

void
vec_mul(Vec *v, float scalar, Vec *r_v);

float
vec_dot(const Vec *a, const Vec *b);

float
vec_len(const Vec *v);

void
vec_cross(const Vec *a, const Vec *b, Vec *r_v);

void
vec_norm(Vec *v);
