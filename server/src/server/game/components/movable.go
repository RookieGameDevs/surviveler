/*
 * Surviveler entity package
 * types definitions
 */
package components

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

/*
 * futurePos computes a future position.
 *
 * It computes the position we would have by following given direction
 * for a given amount of time, at given speed, starting from given position.
 * It doesn't assign the position, so that this method can be used for
 * actual movement as well as movement prediction.
 */
func (me *Movable) futurePos(startPos, direction math.Vec2, speed float64, dt time.Duration) math.Vec2 {
	// compute distance to be covered as time * speed
	distance := dt.Seconds() * me.Speed
	// compute new position after moving given distance in wanted direction
	return startPos.Add(direction.Mul(distance))
}

func (me *Movable) collisionsCheck(dt time.Duration, pos math.Vec2) *game.EntitySet {
	set := me.world.SpatialQuery(me.BoundingBox())
	if !set.Contains(me.ent) {
		panic("collision check failed to find ourselves... :-(")
	}
	set.Remove(me.ent)
	return set
}

/*
 * Move updates the movable position regarding a time delta
 *
 * Move returns true if the position has actually been modified
 */
func (me *Movable) Move(dt time.Duration) (hasMoved bool) {
	// get next waypoint
	if wp, exists := me.waypoints.Peek(); exists {

		// compute translation and direction vectors
		xlate := wp.Sub(me.Pos)
		distToDest := xlate.Len()
		direction := xlate.Normalize()

		// compute our next position, by moving in direction of the waypoint
		newPos := me.futurePos(me.Pos, direction, me.Speed, dt)

		// this is the distance we would travel to go there
		distMove := newPos.Sub(me.Pos).Len()

		// check against edge-cases
		isNan := gomath.IsNaN(distMove) || gomath.IsNaN(distToDest) ||
			gomath.IsNaN(direction.Len()) || gomath.Abs(distMove-distToDest) < 1e-3
		if distMove > distToDest || isNan {
			// we crossed the waypoint, or are really close
			me.Pos = *wp
			if _, exists := me.waypoints.Peek(); exists {
				me.waypoints.Pop()
			}
		} else {
			// actual move
			me.Pos = newPos
		}
		hasMoved = true
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
