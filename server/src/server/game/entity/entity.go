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
 * Entity is the interface that represents stateful game objects
 */
type Entity interface {
	GetState() EntityState
}

type MovableEntity struct {
	Pos   math.Vec2 // current position
	Speed float32   // speed
}
