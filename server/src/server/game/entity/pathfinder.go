/*
 * Surviveler entity package
 * pathfinder interface and implementation
 */
package entity

import (
	"server/math"
)

/*
 * PathFinder is the interface implemented by objects that generate paths on a
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
