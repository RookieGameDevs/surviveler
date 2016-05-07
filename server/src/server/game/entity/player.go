/*
 * Surviveler entity package
 * player
 */
package entity

import (
	"time"
)

type Player struct {
	XPos, YPos         float32
	DestXPos, DestYPos float32
}

func (p *Player) Update(dt time.Duration) {
	p.XPos = 3
	p.YPos = 4
}

func (p *Player) SetDestination(xpos, ypos float32) {
	p.DestXPos = xpos
	p.DestYPos = ypos
}

func (p *Player) GetDestination() (xpos, ypos float32) {
	return p.DestXPos, p.DestYPos
}
