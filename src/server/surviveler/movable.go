/*
 * Surviveler package
 * movable type definition
 */
package surviveler

import (
	"time"

	"github.com/aurelien-rainone/gogeo/f32/d2"
	"github.com/aurelien-rainone/math32"
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
	Pos       d2.Vec2 // current position
	Speed     float32 // speed
	waypoints *VecStack
}

/*
 * NewMovable constructs a new movable
 */
func NewMovable(pos d2.Vec2, speed float32) *Movable {
	return &Movable{
		Pos:       pos,
		Speed:     speed,
		waypoints: newVecStack(),
	}
}

func (me *Movable) findMicroPath(wp d2.Vec2) (path Path, found bool) {
	// for now for simplicity, the micro path is the direct path to the next
	// waypoint
	return Path{wp}, true
}

func (me Movable) ComputeMove(org d2.Vec2, dt time.Duration) d2.Vec2 {
	// update position on the player path
	if dst, exists := me.waypoints.Peek(); exists {
		// compute distance to be covered as time * speed
		distance := float32(dt.Seconds()) * me.Speed
		// compute translation and direction vectors
		dir := dst.Sub(org)
		b := dir.Len()
		dir.Normalize()

		// compute next position
		pos := org.Add(dir.Scale(distance))
		a := pos.Sub(org).Len()

		// check against edge-cases
		isNan := math32.IsNaN(a) || math32.IsNaN(b) || math32.IsNaN(dir.Len()) || math32.Abs(a-b) < 1e-3

		if a > b || isNan {
			return dst
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
		distance := float32(dt.Seconds()) * me.Speed

		for {
			// compute translation and direction vectors
			dir := dst.Sub(me.Pos)
			b := dir.Len()
			dir.Normalize()

			// compute new position
			pos := me.Pos.Add(dir.Scale(distance))
			a := pos.Sub(me.Pos).Len()

			// check against edge-cases
			isNan := math32.IsNaN(a) || math32.IsNaN(b) || math32.IsNaN(dir.Len()) || math32.Abs(a-b) < 1e-3

			hasMoved = true
			if a > b || isNan {
				me.Pos = dst
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
func (me *Movable) SetPath(path Path) {
	// empty the waypoint stack
	for ; me.waypoints.Len() != 0; me.waypoints.Pop() {
	}

	// fill it with waypoints from the macro-path
	for i := range path {
		wp := path[i]
		me.waypoints.Push(wp)
	}
}

func (me *Movable) NextWaypoints() Path {
	path := make(Path, maxNextWaypoints)
	for i, wp := range me.waypoints.PeekN(maxNextWaypoints) {
		path[i] = wp
	}
	return path
}

func (me *Movable) HasReachedDestination() bool {
	return me.waypoints.Len() == 0
}

func (me *Movable) Rectangle() d2.Rectangle {
	return d2.RectFromCircle(me.Pos, 0.5)
}
