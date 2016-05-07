/*
 * Surviveler entity package
 * types definitions
 */
package entity

import (
	"time"
)

/*
 * Updater is the interface implemented by an game object that accepts the
 * delta time in order to update itself
 */
type Updater interface {
	Update(dt time.Duration)
}

/*
 * Mover is the interface implemented by a movable game object. It handles
 * setting and retrieving of its final destination. A Mover must implement
 * the Updater interface
 */
type Mover interface {
	SetDestination(xpos, ypos float32)
	GetDestination() (xpos, ypos float32)
}
