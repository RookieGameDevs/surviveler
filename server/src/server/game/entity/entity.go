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

/*
 * PathFinder is the interface implemented by objects that generate paths on
 * map
 */
type PathFinder interface {
	SetOrigin(org math.Vec2)
	SetDestination(dst math.Vec2)
	GetCurrentDestination() math.Vec2
}

type BasicPathFinder struct {
	org math.Vec2
	dst math.Vec2
}

func (p *BasicPathFinder) SetOrigin(org math.Vec2) {
	p.org = org
}

func (p *BasicPathFinder) SetDestination(dst math.Vec2) {
	p.dst = dst
}

func (p *BasicPathFinder) GetCurrentDestination() math.Vec2 {
	return p.dst
}
