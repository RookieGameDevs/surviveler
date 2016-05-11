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
 * Updater is the interface implemented by objects that have an Update method,
 * called at every tick
 */
type Updater interface {
	Update(dt time.Duration)
}

/*
 * Positioner is the interface implemented by objects aware of a position
 */
type Positioner interface {
	SetPos(pos math.Vec2)
	GetPos() math.Vec2
}

/*
 * Mover is the interface implemented by objects that know how to update an
 * object's position. Implements Updater and Positioner interfaces. The
 * Positioner interface allows to manage the final destination, Updater for
 * actual moving and GetSnapshot in order to retrieve current position
 */
type Mover interface {
	Updater
	Positioner
	// Set current speed
	SetSpeed(s float32)
	// Get current speed
	GetSpeed() float32
	// Set destination
	SetDestPos(pos math.Vec2)
	// Get destination
	GetDestPos() math.Vec2
	// know if destination has been reached
	HasReachedDestination() bool
}
