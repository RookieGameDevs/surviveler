/*
 * Surviveler entity package
 * types definitions
 */
package entity

import (
	"server/math"
	"time"
)

/*
 * Enumeration of possible entity types.
 */
type EntityType uint8

/*
 * Entity type identifiers.
 */
const (
	TypeTank EntityType = 0 + iota
	TypeProgrammer
	TypeEngineer
	TypeZombie
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
	GetType() EntityType
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
	// update position on the player path
	if len(me.curPath) > 0 {
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
