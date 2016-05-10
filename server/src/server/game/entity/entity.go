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
	// Set Current Speed
	SetSpeed(s float32)
	// Get a snapshot of current position, action
	GetSnapshot() *ActionSnapshot
	// know if destination has been reached
	HasReachedDestination() bool
}

/*
 * ActionSnapshot represents the snapshot of an entity's current action.
 * Example: an entity 1, currently in room A, its main goal is 'Kill Entity 2'.
 * But entity 2 is in another room, so entity 1 current action is 'Walking to
 * room B' and thus can be represented by an ActionSnapshot struct
 */
type ActionSnapshot struct {
	// current entity position
	CurPos math.Vec2
	// current destination
	DestPos math.Vec2
	// current speed
	CurSpeed float32
	// expected timestamp at destination arrival (may vary over time)
	DestTstamp int64
}
