package d2

import "fmt"

// Rectangler is the interface implemented by objects that can return a
// rectangular representation of themselves in 2D space.
type Rectangler interface {
	Rectangle() Rectangle
}

// A Rectangle is defined by 2 points, Min and Max, represented by 2 Vec2.
type Rectangle struct {
	Min, Max Vec2
}

// ZR is the zero Rectangle.
var ZR Rectangle

func init() {
	// allocate the vector of the ZR rectangle
	ZR = Rectangle{Min: Vec2{0, 0}, Max: Vec2{0, 0}}
}

// Rect is shorthand for Rectangle{Vec2(x0, y0), Vec2(x1, y1)}. The returned
// rectangle has minimum and maximum coordinates swapped if necessary so that
// it is well-formed.
func Rect(x0, y0, x1, y1 float32) Rectangle {
	if x0 > x1 {
		x0, x1 = x1, x0
	}
	if y0 > y1 {
		y0, y1 = y1, y0
	}
	return Rectangle{Vec2{x0, y0}, Vec2{x1, y1}}
}

// RectWH returns a rectangle whose origin is Vec2{x,y}, w and h are its width
// and height.
func RectWH(x, y, w, h float32) Rectangle {
	return Rectangle{
		Min: Vec2{x, y},
		Max: Vec2{x + w, y + h},
	}
}

// RectFromCircle returns the minimum rectangle that contains the circle of
// center c and radius r
func RectFromCircle(c Vec2, r float32) Rectangle {
	return RectWH(c[0]-r, c[1]-r, 2*r, 2*r)
}

func NewRect() Rectangle {
	return Rectangle{
		Min: Vec2{0, 0},
		Max: Vec2{0, 0},
	}
}

// CopyRect allocates and returns a new Rectangle that is the copy of r.
func CopyRect(r Rectangle) Rectangle {
	r1 := NewRect()
	r1.Min.Assign(r.Min)
	r1.Max.Assign(r.Max)
	return r1
}

// Returns the center of r.
func (r Rectangle) Center() Vec2 {
	return r.Size().Scale(0.5).Add(r.Min)
}

// Dx returns r's width.
func (r Rectangle) Dx() float32 {
	return r.Max[0] - r.Min[0]
}

// Dy returns r's height.
func (r Rectangle) Dy() float32 {
	return r.Max[1] - r.Min[1]
}

// Size returns r's width and height.
func (r Rectangle) Size() Vec2 {
	return Vec2{
		r.Max[0] - r.Min[0],
		r.Max[1] - r.Min[1],
	}
}

// Add returns the rectangle r translated by v.
func (r Rectangle) Add(v Vec2) Rectangle {
	return Rectangle{
		Vec2{r.Min[0] + v[0], r.Min[1] + v[1]},
		Vec2{r.Max[0] + v[0], r.Max[1] + v[1]},
	}
}

// Sub returns the rectangle r translated by -v.
func (r Rectangle) Sub(v Vec2) Rectangle {
	return Rectangle{
		Vec2{r.Min[0] - v[0], r.Min[1] - v[1]},
		Vec2{r.Max[0] - v[0], r.Max[1] - v[1]},
	}
}

// Inset returns the rectangle r inset by n, which may be negative. If either
// of r's dimensions is less than 2*n then an empty rectangle near the center
// of r will be returned.
func (r Rectangle) Inset(n float32) Rectangle {
	if r.Dx() < 2*n {
		r.Min[0] = (r.Min[0] + r.Max[0]) / 2
		r.Max[0] = r.Min[0]
	} else {
		r.Min[0] += n
		r.Max[0] -= n
	}
	if r.Dy() < 2*n {
		r.Min[1] = (r.Min[1] + r.Max[1]) / 2
		r.Max[1] = r.Min[1]
	} else {
		r.Min[1] += n
		r.Max[1] -= n
	}
	return r
}

// Intersect returns the largest rectangle contained by both r and s. If the
// two rectangles do not overlap then the zero rectangle will be returned.
func (r Rectangle) Intersect(s Rectangle) Rectangle {
	ir := Rect(r.Min[0], r.Min[1], r.Max[0], r.Max[1])
	if ir.Min[0] < s.Min[0] {
		ir.Min[0] = s.Min[0]
	}
	if ir.Min[1] < s.Min[1] {
		ir.Min[1] = s.Min[1]
	}
	if ir.Max[0] > s.Max[0] {
		ir.Max[0] = s.Max[0]
	}
	if ir.Max[1] > s.Max[1] {
		ir.Max[1] = s.Max[1]
	}
	if ir.Min[0] > ir.Max[0] || ir.Min[1] > ir.Max[1] {
		return ZR
	}
	return ir
}

// Union returns the smallest rectangle that contains both r and s.
func (r Rectangle) Union(s Rectangle) Rectangle {
	if r.Empty() {
		return s
	}
	if s.Empty() {
		return r
	}
	if r.Min[0] > s.Min[0] {
		r.Min[0] = s.Min[0]
	}
	if r.Min[1] > s.Min[1] {
		r.Min[1] = s.Min[1]
	}
	if r.Max[0] < s.Max[0] {
		r.Max[0] = s.Max[0]
	}
	if r.Max[1] < s.Max[1] {
		r.Max[1] = s.Max[1]
	}
	return r
}

// Empty reports whether the rectangle contains no points.
func (r Rectangle) Empty() bool {
	return r.Min[0] >= r.Max[0] || r.Min[1] >= r.Max[1]
}

// Eq reports whether r and s contain the same set of points. All empty
// rectangles are considered equal.
func (r Rectangle) Eq(s Rectangle) bool {
	return (r.Min.Approx(s.Min) && r.Max.Approx(s.Max)) ||
		r.Empty() && s.Empty()
}

// Overlaps reports whether r and s have a non-empty intersection.
func (r Rectangle) Overlaps(s Rectangle) bool {
	return !r.Empty() && !s.Empty() &&
		r.Min[0] < s.Max[0] && s.Min[0] < r.Max[0] &&
		r.Min[1] < s.Max[1] && s.Min[1] < r.Max[1]
}

// Contains reports whether rectangle r contains point p
func (r Rectangle) Contains(p Vec2) bool {
	return r.Min[0] <= p[0] && p[0] < r.Max[0] &&
		r.Min[1] <= p[1] && p[1] < r.Max[1]
}

// In reports whether Rectangle r is contained in s.
func (r Rectangle) In(s Rectangle) bool {
	if r.Empty() {
		return true
	}
	// Note that r.Max is an exclusive bound for r, so that r.In(s)
	// does not require that r.Max.In(s).
	return s.Min[0] <= r.Min[0] && r.Max[0] <= s.Max[0] &&
		s.Min[1] <= r.Min[1] && r.Max[1] <= s.Max[1]
}

// Canon returns the canonical version of r. The returned rectangle has minimum
// and maximum coordinates swapped if necessary so that it is well-formed.
func (r Rectangle) Canon() Rectangle {
	if r.Max[0] < r.Min[0] {
		r.Min[0], r.Max[0] = r.Max[0], r.Min[0]
	}
	if r.Max[1] < r.Min[1] {
		r.Min[1], r.Max[1] = r.Max[1], r.Min[1]
	}
	return r
}

// String returns a string representation of r.
func (r Rectangle) String() string {
	return fmt.Sprintf("(Min:%v,Max:%v)", r.Min, r.Max)
}
