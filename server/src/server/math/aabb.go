package math

import (
	gomath "math"
)

type BoundingBoxer interface {
	BoundingBox() BoundingBox
}

// Use NewBoundingBox() to construct a BoundingBox object
type BoundingBox struct {
	MinX, MaxX, MinY, MaxY float64
}

func NewBoundingBox(xa, xb, ya, yb float64) BoundingBox {
	return BoundingBox{gomath.Min(xa, xb), gomath.Max(xa, xb), gomath.Min(ya, yb), gomath.Max(ya, yb)}
}

func NewBoundingBoxFromCircle(center Vec2, radius float64) BoundingBox {
	x, y := center.Elem()
	return BoundingBox{x - radius, x + radius, y - radius, y + radius}
}
func (b BoundingBox) SizeX() float64 {
	return b.MaxX - b.MinX
}

func (b BoundingBox) SizeY() float64 {
	return b.MaxY - b.MinY
}

// Returns true if o intersects this
func (b BoundingBox) Intersects(o BoundingBox) bool {
	return b.MinX < o.MaxX && b.MinY < o.MaxY &&
		b.MaxX > o.MinX && b.MaxY > o.MinY
}

// Returns true if o is within this
func (b BoundingBox) Contains(o BoundingBox) bool {
	return b.MinX <= o.MinX && b.MinY <= o.MinY &&
		b.MaxX >= o.MaxX && b.MaxY >= o.MaxY
}
