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
 * Movable is the *moving part* of an entity.
 *
 * This struct is meant to be used as a component of another higher-level entity,
 * and take care of its movement. It accepts a path and updates the pos to move
 * alongside it
 */
type Movable struct {
	Pos                   math.Vec2 // current position
	Speed                 float64   // speed
	curPath               math.Path // player path
	curPathIdx            int       // index in the path
	hasReachedDestination bool
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

func (me *Movable) Update(dt time.Duration) {
	// update position on the player path
	if me.curPathIdx >= 0 && me.curPathIdx < len(me.curPath) {
		// get sub-destination (current path segment)
		dst := me.curPath[me.curPathIdx]

		// compute translation and direction vectors
		xlate := dst.Sub(me.Pos)
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
			me.Pos = dst
			me.curPathIdx--
			if me.curPathIdx < 0 {
				me.hasReachedDestination = true
			} else {
				dst = me.curPath[me.curPathIdx]
			}
		} else {
			me.Pos = newPos
		}
	} else {
		me.hasReachedDestination = true
		me.curPathIdx = 0
	}
}

/*
 * SetPath defines the path that the movable entity should follow along
 */
func (me *Movable) SetPath(path math.Path) {
	pLen := len(path)
	if pLen > 0 {
		me.Pos = path[pLen-1]
		if pLen > 1 {
			me.hasReachedDestination = false
			me.curPath = path[:pLen-1]
			// the tail element of the path represents the starting point, it's
			// also the position the entity is already located, so we don't want
			// to send this position to the client
			me.curPathIdx = pLen - 2
		} else {
			me.hasReachedDestination = true
			me.curPath = math.Path{}
			me.curPathIdx = -1
		}
	}
}

func (me *Movable) Path(maxLen int) math.Path {
	count := me.curPathIdx + 1
	if maxLen > 0 {
		count = math.IMin(count, maxLen)
	}

	// allocate a new array and store the waypoints in reverse order
	path := make(math.Path, 0)
	for i, j := 0, me.curPathIdx; i < count; i, j = i+1, j-1 {
		path = append(path, me.curPath[j])
	}
	return path
}

func (me *Movable) HasReachedDestination() bool {
	return me.hasReachedDestination
}
