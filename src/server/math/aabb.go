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

func (b BoundingBox) TopLeft() Vec2 {
	return Vec2{b.MinX, b.MinY}
}

func (b BoundingBox) BottomRight() Vec2 {
	return Vec2{b.MaxX, b.MaxY}
}

func (b BoundingBox) SizeX() float64 {
	return b.MaxX - b.MinX
}

func (b BoundingBox) SizeY() float64 {
	return b.MaxY - b.MinY
}

func (b BoundingBox) Center() Vec2 {
	return Vec2{(b.MinX + b.MaxX) / 2, (b.MinY + b.MaxY) / 2}
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

// Xlate performs a translation of the bounding box
func (b *BoundingBox) Xlate(v Vec2) {
	min := Vec2{b.MinX, b.MinY}
	max := Vec2{b.MaxX, b.MaxY}
	b.MinX, b.MinY = min.Add(v).Elem()
	b.MaxX, b.MaxY = max.Add(v).Elem()
}
