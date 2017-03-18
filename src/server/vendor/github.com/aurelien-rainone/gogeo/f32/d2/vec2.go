package d2

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/aurelien-rainone/math32"
)

// Vec2 is a 2 dimensions vector. It is made up of a slice of 32 bits floating
// points numbers.
//
// Depending on the context, a Vec2 can also represent a point in 2D space.
type Vec2 []float32

// NewVec2 allocates and returns a new Vec2 where each component has its zero
// value.
func NewVec2() Vec2 {
	return make(Vec2, 2)
}

// NewVec2From allocates and returns a new Vec2 that is the copy of v1.
func NewVec2From(v1 Vec2) Vec2 {
	return Vec2{v1[0], v1[1]}
}

// NewVec2XY allocates and returns Vec2{x, y}.
func NewVec2XY(x, y float32) Vec2 {
	return Vec2{x, y}
}

// component access

// X returns the X component of v.
func (v Vec2) X() float32 {
	return v[0]
}

// Y returns the Y component of v.
func (v Vec2) Y() float32 {
	return v[1]
}

// X sets the X component of v.
func (v Vec2) SetX(x float32) {
	v[0] = x
}

// Y sets the Y component of v.
func (v Vec2) SetY(y float32) {
	v[1] = y
}

// Vec2 functions

// Vec2Add performs a vector addition. dest = v1 + v2
//
//     dest   [out] The result vector.
//     v1     [in]  The base vector.
//     v2     [in]  The vector to add to v1.
func Vec2Add(dest, v1, v2 Vec2) {
	dest[0] = v1[0] + v2[0]
	dest[1] = v1[1] + v2[1]
}

// Vec2SAdd performs a scaled vector addition. dest = v1 + (v2 * s)
//
//     dest   [out] The result vector.
//     v1     [in]  The base vector.
//     v1     [in]  The vector to scale and add to v1.
//     s      [in]  The amount to scale v2 by before adding to v1.
func Vec2SAdd(dest, v1, v2 Vec2, s float32) {
	dest[0] = v1[0] + v2[0]*s
	dest[1] = v1[1] + v2[1]*s
}

// Vec2Sub performs a vector subtraction. dest = v1 - v2.
//
//     dest  [out]  The result vector.
//     v1    [in]   The base vector.
//     v2    [in]   The vector to subtract from v1.
func Vec2Sub(dest, v1, v2 Vec2) {
	dest[0] = v1[0] - v2[0]
	dest[1] = v1[1] - v2[1]
}

// Vec2Scale scales a vector by value t. dest = v * t
//
//     dest  [out]  The result vector.
//     v     [in]   The vector to scale.
//     t     [in]   The scaling factor.
func Vec2Scale(dest, v Vec2, t float32) {
	dest[0] = v[0] * t
	dest[1] = v[1] * t
}

// Vec2Min selects the minimum value of each element from the specified vectors.
//
//     mn  [in,out] A vector, will be updated with the result.
//     v   [in]     A vector.
func Vec2Min(mn, v Vec2) {
	mn[0] = math32.Min(mn[0], v[0])
	mn[1] = math32.Min(mn[1], v[1])
}

// Vec2Max selects the maximum value of each element from the specified vectors.
//
//     mx  [in,out] A vector, will be updated with the result.
//     v   [in]     A vector.
func Vec2Max(mx, v Vec2) {
	mx[0] = math32.Max(mx[0], v[0])
	mx[1] = math32.Max(mx[1], v[1])
}

// Vec2Lerp performs a linear interpolation between two vectors. v1 toward v2
//
//     dest  [out]  The result vector.
//     v1    [in]   The starting vector.
//     v2    [in]   The destination vector.
//     t     [in]   The interpolation factor. [Limits: 0 <= value <= 1.0]
func Vec2Lerp(dest, v1, v2 Vec2, t float32) {
	dest[0] = v1[0] + (v2[0]-v1[0])*t
	dest[1] = v1[1] + (v2[1]-v1[1])*t
}

// Vec2 methods

// Add returns a new vector that is the result of v + v1.
//
// It allocates a new vector/slice.
func (v Vec2) Add(v1 Vec2) Vec2 {
	return NewVec2XY(
		v[0]+v1[0],
		v[1]+v1[1],
	)
}

// SAdd returns a new vector that is the result of v + (v1 * s).
//
// It allocates a new vector/slice.
func (v Vec2) SAdd(v1 Vec2, s float32) Vec2 {
	return NewVec2XY(
		v[0]+v1[0]*s,
		v[1]+v1[1]*s,
	)
}

// Sub returns a new vector that is the result of v - v1.
//
// It allocates a new vector/slice.
func (v Vec2) Sub(v1 Vec2) Vec2 {
	return NewVec2XY(
		v[0]-v1[0],
		v[1]-v1[1],
	)
}

// Scale returns a new vector that is the result of v * t
func (v Vec2) Scale(t float32) Vec2 {
	return NewVec2XY(
		v[0]*t,
		v[1]*t,
	)
}

// Assign assign the component of v1 to v. v = v1
func (v Vec2) Assign(v1 Vec2) {
	v[0] = v1[0]
	v[1] = v1[1]
}

// LenSqr derives the scalar scalar length of the vector. (len)
func (v Vec2) Len() float32 {
	return math32.Sqrt(v[0]*v[0] + v[1]*v[1])
}

// LenSqr derives the square of the scalar length of the vector. (len * len)
func (v Vec2) LenSqr() float32 {
	return v[0]*v[0] + v[1]*v[1]
}

// Dist returns the distance between v and v1. d = dist(v, v2)
func (v Vec2) Dist(v1 Vec2) float32 {
	dx := v1[0] - v[0]
	dy := v1[1] - v[1]
	return math32.Sqrt(dx*dx + dy*dy)
}

// DistSqr returns the square of the distance between two points.
func (v Vec2) DistSqr(v1 Vec2) float32 {
	dx := v1[0] - v[0]
	dy := v1[1] - v[1]
	return dx*dx + dy*dy
}

// Normalize normalizes the vector.
func (v Vec2) Normalize() {
	d := 1.0 / math32.Sqrt(v[0]*v[0]+v[1]*v[1])
	v[0] *= d
	v[1] *= d
}

// Lerp returns the result vector of a linear interpolation between two
// vectors. v toward v1.
//
// The interpolation factor t should be comprised betwenn 0 and 1.0.
// [Limits: 0 <= value <= 1.0]
func (v Vec2) Lerp(dest, v1 Vec2, t float32) Vec2 {
	return Vec2{
		v[0] + (v1[0]-v[0])*t,
		v[1] + (v1[1]-v[1])*t,
	}
}

// Dot derives the dot product of two vectors. v . v1
func (v Vec2) Dot(v1 Vec2) float32 {
	return v[0]*v1[0] + v[1]*v1[1]
}

// Approx reports wether v and v1 are approximately equal.
//
// Element-wise approximation uses math32.Approx()
func (v Vec2) Approx(v1 Vec2) bool {
	return math32.Approx(v[0], v1[0]) &&
		math32.Approx(v[1], v1[1])
}

// String returns a string representation of v like "(3,4)".
func (v Vec2) String() string {
	if len(v) < 2 {
		return fmt.Sprintf("Vec2(!not-allocated)")
	}
	return fmt.Sprintf("(%.4g,%.4g)", v[0], v[1])
}

func (v *Vec2) Set(s string) error {
	cur := 0
	for _, ss := range strings.Split(s, ",") {
		fmt.Println("ss", ss)
		if f, err := strconv.ParseFloat(ss, 32); err != nil {
			return fmt.Errorf("error parsing %v, %v", ss, err)
		} else {
			(*v)[cur] = float32(f)
			cur++
		}
	}
	return nil
}
