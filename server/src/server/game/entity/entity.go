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
 * Updater is the interface implemented by objects having an Update method,
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
 * Mover is the interface implemented by objects knowing how to move,
 * themselves or other objects, at every tick.
 */
type Mover interface {
	Updater
	Positioner
	GetDestination() math.Vec2
	SetDestination(pos math.Vec2)
	SetSpeed(s float32)
	GetSpeed() float32
}
