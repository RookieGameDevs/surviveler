/*
 * Surviveler package
 * movable type definition
 */
package surviveler

import (
	gomath "math"
	"server/math"
	"time"
)

/*
 * Number of next waypoints to return in NextWaypoints
 */
const maxNextWaypoints = 2

/*
 * Movable is the *moving part* of an entity.
 *
 * This struct is meant to be used as a component of another higher-level entity,
 * and take care of its movement. It accepts a path and updates the pos to move
 * alongside it
 */
type Movable struct {
	Pos       math.Vec2 // current position
	Speed     float64   // speed
	waypoints *math.VecStack
}

/*
 * NewMovable constructs a new movable
 */
func NewMovable(pos math.Vec2, speed float64) *Movable {
	return &Movable{
		Pos:       pos,
		Speed:     speed,
		waypoints: math.NewVecStack(),
	}
}

func (me *Movable) findMicroPath(wp math.Vec2) (path math.Path, found bool) {
	// for now for simplicity, the micro path is the direct path to the next
	// waypoint
	return math.Path{wp}, true
}

func (me Movable) ComputeMove(org math.Vec2, dt time.Duration) math.Vec2 {
	// update position on the player path
	if dst, exists := me.waypoints.Peek(); exists {
		// compute distance to be covered as time * speed
		distance := dt.Seconds() * me.Speed
		// compute translation and direction vectors
		t := dst.Sub(org)
		b := t.Len()
		dir := t.Normalize()

		// compute next position
		pos := org.Add(dir.Mul(distance))
		a := pos.Sub(org).Len()

		// check against edge-cases
		isNan := gomath.IsNaN(a) || gomath.IsNaN(b) || gomath.IsNaN(dir.Len()) || gomath.Abs(a-b) < 1e-3

		if a > b || isNan {
			return *dst
		} else {
			return pos
		}
	}
	return org
}

/*
 * Move updates the movable position regarding a time delta
 *
 * Move returns true if the position has actually been modified
 */
func (me *Movable) Move(dt time.Duration) (hasMoved bool) {
	// update position on the player path
	if dst, exists := me.waypoints.Peek(); exists {
		// compute distance to be covered as time * speed
		distance := dt.Seconds() * me.Speed

		for {
			// compute translation and direction vectors
			t := dst.Sub(me.Pos)
			b := t.Len()
			dir := t.Normalize()

			// compute new position
			pos := me.Pos.Add(dir.Mul(distance))
			a := pos.Sub(me.Pos).Len()

			// check against edge-cases
			isNan := gomath.IsNaN(a) || gomath.IsNaN(b) || gomath.IsNaN(dir.Len()) || gomath.Abs(a-b) < 1e-3

			hasMoved = true
			if a > b || isNan {
				me.Pos = *dst
				if _, exists = me.waypoints.Peek(); exists {
					me.waypoints.Pop()
					break
				} else {
					break
				}

				if isNan {
					break
				}

				distance = a - b
			} else {
				me.Pos = pos
				break
			}
		}
	}
	return
}

/*
 * SetPath sets the path that the movable entity should follow along
 *
 * It replaces and cancel the current path, if any.
 */
func (me *Movable) SetPath(path math.Path) {
	// empty the waypoint stack
	for ; me.waypoints.Len() != 0; me.waypoints.Pop() {
	}

	// fill it with waypoints from the macro-path
	for i := range path {
		wp := path[i]
		me.waypoints.Push(&wp)
	}
}

func (me *Movable) NextWaypoints() math.Path {
	path := math.Path{}
	for _, wp := range me.waypoints.PeekN(maxNextWaypoints) {
		path = append(path, *wp)
	}
	return path
}

func (me *Movable) HasReachedDestination() bool {
	return me.waypoints.Len() == 0
}

func (me *Movable) BoundingBox() math.BoundingBox {
	return math.NewBoundingBoxFromCircle(me.Pos, 0.5)
}
