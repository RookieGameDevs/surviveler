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
 * Number of next waypoints to return in NextPos
 */
const maxNextPositions = 2

/*
 * Movable is the *moving part* of an entity.
 *
 * This struct is meant to be used as a component of another higher-level entity,
 * and take care of its movement. It accepts a path and updates the pos to move
 * alongside it
 */
type Movable struct {
	Pos                   math.Vec2 // current position
	Speed                 float64   // speed
	hasReachedDestination bool
	waypoints             *math.VecStack
}

func (me *Movable) Init() {
	me.waypoints = math.NewVecStack()
}

func (me *Movable) findMicroPath(wp math.Vec2) (path math.Path, found bool) {
	// for now for simplicity, the micro path is the direct path to the next
	// waypoint
	return math.Path{wp}, true
}

/*
 * nextPos computes the next position and returns it.
 *
 * It computes the position we would have by following given direction
 * for a given amount of time, at given speed, starting from given position.
 * It doesn't assign the position, so that this method can be used for
 * actual movement as well as movement prediction.
 */
func (me *Movable) nextPos(startPos, direction math.Vec2, speed float64, dt time.Duration) math.Vec2 {
	// compute distance to be covered as time * speed
	distance := dt.Seconds() * me.Speed
	// compute new position after moving given distance in wanted direction
	return startPos.Add(direction.Mul(distance))
}

func (me *Movable) move(dt time.Duration) {
	// get next waypoint
	if wp, exists := me.waypoints.Peek(); exists {
		// compute translation and direction vectors
		xlate := wp.Sub(me.Pos)
		distToDest := xlate.Len()
		direction := xlate.Normalize()

		// compute our next position, by moving in direction of the waypoint
		newPos := me.nextPos(me.Pos, direction, me.Speed, dt)

		// this is the distance we would travel to go there
		distMove := newPos.Sub(me.Pos).Len()

		// check against edge-cases
		isNan := gomath.IsNaN(distMove) || gomath.IsNaN(distToDest) ||
			gomath.IsNaN(direction.Len()) || gomath.Abs(distMove-distToDest) < 1e-3
		if distMove > distToDest || isNan {
			me.Pos = *wp
			if _, exists := me.waypoints.Peek(); !exists {
				//me.hasReachedDestination = true
			} else {
				me.waypoints.Pop()
			}
		} else {
			me.Pos = newPos
		}
	} else {
		// no more waypoints!
		me.hasReachedDestination = true
	}
}

func (me *Movable) Update(dt time.Duration) {

	// movement update
	me.move(dt)
}

/*
 * SetPath defines the path that the movable entity should follow along
 */
func (me *Movable) SetPath(path math.Path) {

	// empty the waypoint stack
	for ; me.waypoints.Len() > 1; me.waypoints.Pop() {
	}

	// fill it with waypoints from the macro-path
	for i := range path {
		if i > 0 {
			wp := path[i]
			me.waypoints.Push(&wp)
		}
	}
	me.hasReachedDestination = false
}

func (me *Movable) NextPos() math.Path {
	path := math.Path{}
	for _, wp := range me.waypoints.PeekN(maxNextPositions) {
		path = append(path, *wp)
	}
	return path
}

func (me *Movable) HasReachedDestination() bool {
	return me.hasReachedDestination
}
