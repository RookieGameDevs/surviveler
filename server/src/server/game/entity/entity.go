/*
 * Surviveler entity package
 * types
 */
package entity

import (
	"time"
)

/*
 * Updater is the interface implemented by an game object that updates itself
 */
type Updater interface {
	Update(dt time.Duration)
}

type Player struct {
	XPos, YPos float32
}

func (p *Player) Update(dt time.Duration) {
	p.XPos = 3
	p.YPos = 4
}
