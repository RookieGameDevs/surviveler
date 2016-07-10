package math

import (
	gomath "math"
)

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

type BoundingBoxer interface {
	BoundingBox() BoundingBox
}
