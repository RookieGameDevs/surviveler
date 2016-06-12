/*
 * Surviveler entity package
 * types definitions
 */
package entity

import (
	gomath "math"
	"server/math"
	"time"
)

/*
 * Updater is the interface implemented by objects that have an Update method,
 * called at every tick
 */
type Updater interface {
	Update(dt time.Duration)
}

/*
 * Entity is the interface that represents stateful game objects
 */
type Entity interface {
	GetState() EntityState
	Updater
}

/*
 * MovableEntity is the *moving part* of an entity.
 *
 * This struct is meant to be used as a component of another higher-level entity,
 * and take care of its movement. It accepts a path and updates the pos to move
 * alongside it. It implements the Entity and Updater interfaces
 */
type MovableEntity struct {
	Pos                   math.Vec2 // current position
	Speed                 float64   // speed
	curPath               math.Path // player path
	curPathIdx            int       // index in the path
	hasReachedDestination bool
}

func (me *MovableEntity) Update(dt time.Duration) {
	// update position on the player path
	pathLength := len(me.curPath)
	if pathLength > 0 {
		// get sub-destination (current path segment)
		subDst := me.curPath[me.curPathIdx]

		// compute translation vector
		moveVec := subDst.Sub(me.Pos).Normalize()
		me.Pos = me.Pos.Add(moveVec.Mul(me.Speed * dt.Seconds()))

		if gomath.Abs(subDst[0]-me.Pos[0]) <= 0.01 &&
			gomath.Abs(subDst[1]-me.Pos[1]) <= 0.01 {
			// reached current sub-destination
			me.curPathIdx--
			me.Pos = subDst

			switch {
			case me.curPathIdx < 0:
				// this was the last path segment
				me.hasReachedDestination = true
			}
		}
	}
}

/*
 * SetPath defines the path that the movable entity should follow along
 */
func (me *MovableEntity) SetPath(path math.Path) {
	me.hasReachedDestination = false
	me.curPath = path
	// the tail element of the path represents the starting point, it's also
	// the position the entity is already located, so we don't want to send
	// this position to the client
	me.curPathIdx = len(path) - 2
}
