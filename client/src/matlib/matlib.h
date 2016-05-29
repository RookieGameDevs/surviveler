#pragma once

#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif


typedef struct Mat4 {
	float data[16];
} Mat4;

typedef struct Vec3 {
	float data[3];
} Vec3;

typedef struct Vec4 {
	float data[4];
} Vec4;

void
mat4_mul(const Mat4 *a, const Mat4 *b, Mat4 *r_m);

void
mat4_mul_vec(const Mat4 *m, const Vec4 *v, Vec4 *r_v);

void
mat4_rotate(Mat4 *m, const Vec3 *v, float angle);

void
mat4_scale(Mat4 *m, float sx, float sy, float sz);

void
mat4_scalev(Mat4 *m, const Vec3 *sv);

void
mat4_translate(Mat4 *m, float tx, float ty, float tz);

void
mat4_translatev(Mat4 *m, const Vec3 *tv);

void
mat4_ident(Mat4 *m);

int
mat4_inv(Mat4 *m, Mat4 *out_m);

void
mat4_print(const Mat4 *m);

Vec3
vec3(float x, float y, float z);

void
vec3_sum(const Vec3 *a, const Vec3 *b, Vec3 *r_v);

void
vec3_mul(Vec3 *v, float scalar);

float
vec3_len(const Vec3 *v);

void
vec3_norm(Vec3 *v);

float
vec3_dot(const Vec3 *a, const Vec3 *b);

void
vec3_cross(const Vec3 *a, const Vec3 *b, Vec3 *r_v);

Vec4
vec4(float x, float y, float z, float w);

void
vec4_sum(const Vec4 *a, const Vec4 *b, Vec4 *r_v);

void
vec4_mul(Vec4 *v, float scalar);

float
vec4_len(const Vec4 *v);

void
vec4_norm(Vec4 *v);
