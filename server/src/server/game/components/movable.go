/*
 * Surviveler entity package
 * types definitions
 */
package components

import (
	"server/math"
	"time"
)

/*
 * Movable is the *moving part* of an entity.
 *
 * This struct is meant to be used as a component of another higher-level entity,
 * and take care of its movement. It accepts a path and updates the pos to move
 * alongside it. It implements the Entity and Updater interfaces
 */
type Movable struct {
	Pos                   math.Vec2 // current position
	Speed                 float64   // speed
	curPath               math.Path // player path
	curPathIdx            int       // index in the path
	hasReachedDestination bool
}

func (me *Movable) Update(dt time.Duration) {
	// update position on the player path
	if me.curPathIdx >= 0 && me.curPathIdx < len(me.curPath) {
		// get sub-destination (current path segment)
		dst := me.curPath[me.curPathIdx]

		// compute distance to be covered as time * speed
		distance := dt.Seconds() * me.Speed

		for {
			// compute translation and direction vectors
			t := dst.Sub(me.Pos)
			dir := t.Normalize()

			// compute new position
			pos := me.Pos.Add(dir.Mul(distance))
			a := pos.Sub(me.Pos).Len()
			b := t.Len()

			if a > b {
				me.Pos = dst
				me.curPathIdx--
				if me.curPathIdx < 0 {
					me.hasReachedDestination = true
					break
				}
				dst = me.curPath[me.curPathIdx]
				distance = a - b
			} else {
				me.Pos = pos
				break
			}
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
	me.hasReachedDestination = false
	me.curPath = path
	// the tail element of the path represents the starting point, it's also
	// the position the entity is already located, so we don't want to send
	// this position to the client
	me.curPathIdx = len(path) - 2
}

func (me *Movable) GetPath(maxLen int) math.Path {
	// compute the slice bounds of the resulting path
	var to int
	from := me.curPathIdx
	if maxLen <= 0 {
		to = 0
	} else {
		to = math.IMax(0, from-maxLen)
	}

	// allocate a new array and store the waypoints in reverse order
	path := make(math.Path, 1+from-to)
	for i, j := from, 0; i >= to; i, j = i-1, j+1 {
		path[j] = me.curPath[i]
	}
	return path
}

func (me *Movable) HasReachedDestination() bool {
	return me.hasReachedDestination
}
