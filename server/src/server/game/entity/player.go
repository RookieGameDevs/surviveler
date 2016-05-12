/*
 * Surviveler entity package
 * player
 */
package entity

import (
	"server/game/messages"
	"server/math"
	"time"
)

/*
 * Player represents an entity that is controlled by a physical player. It
 * implements the Entity interface.
 */
type Player struct {
	MovableEntity
	Pathfinder PathFinder
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(startX, startY, speed float32) *Player {

	p := new(Player)
	p.Speed = speed
	p.Pathfinder = &BasicPathFinder{}
	p.Pos = math.Vec2{startX, startY}
	p.CurAction = messages.IdleAction
	return p
}

func (p *Player) Update(dt time.Duration) {

	// update position
	if p.CurAction != messages.IdleAction {

		curDst := p.Pathfinder.GetCurrentDestination()

		// compute translation vector
		moveVec := curDst.Sub(p.Pos).Normalize()
		p.Pos = p.Pos.Add(moveVec.Mul(float32(p.Speed * float32(dt.Seconds()))))

		// arrived at destination?
		if p.Pos.ApproxEqualThreshold(curDst, 0.01) {
			// destination reached
			p.CurAction = messages.IdleAction
		}
	}
}

func (p *Player) Move(dst math.Vec2) {
	// setup pathfinding
	p.Pathfinder.SetOrigin(p.Pos)
	p.Pathfinder.SetDestination(dst)
	p.CurAction = messages.MovingAction
}

func (p *Player) GetAction() (messages.ActionType, interface{}) {
	if p.CurAction == messages.IdleAction {
		return messages.IdleAction, messages.IdleActionData{}
	} else {
		dst := p.Pathfinder.GetCurrentDestination()
		return messages.MovingAction, messages.MoveActionData{
			Speed: p.Speed,
			Xpos:  dst[0],
			Ypos:  dst[1],
		}
	}
}
