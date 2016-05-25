/*
 * Surviveler entity package
 * player
 */
package entity

import (
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
	CurAction  ActionType // current action
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(startX, startY, speed float32, pathfinder PathFinder) *Player {
	p := new(Player)
	p.Speed = speed
	p.Pathfinder = pathfinder
	p.Pos = math.Vec2{startX, startY}
	p.CurAction = IdleAction
	return p
}

func (p *Player) Update(dt time.Duration) {
	// update position
	if p.CurAction != IdleAction {

		curDst := p.Pathfinder.GetCurrentDestination()

		// compute translation vector
		moveVec := curDst.Sub(p.Pos).Normalize()
		p.Pos = p.Pos.Add(moveVec.Mul(float32(p.Speed * float32(dt.Seconds()))))

		// arrived at destination?
		if p.Pos.ApproxEqualThreshold(curDst, 0.01) {
			// destination reached
			p.CurAction = IdleAction
		}
	}
}

func (p *Player) Move(dst math.Vec2) {
	// setup pathfinding
	p.Pathfinder.SetOrigin(p.Pos)
	p.Pathfinder.SetDestination(dst)
	p.CurAction = MovingAction
}

func (p *Player) GetState() EntityState {
	// first compile the data depending on current action
	var actionData interface{}
	if p.CurAction == IdleAction {
		actionData = IdleActionData{}
	} else {
		dst := p.Pathfinder.GetCurrentDestination()
		actionData = MoveActionData{
			Speed: p.Speed,
			Xpos:  dst[0],
			Ypos:  dst[1],
		}
	}

	return EntityState{
		Xpos:       p.Pos[0],
		Ypos:       p.Pos[1],
		ActionType: p.CurAction,
		Action:     actionData,
	}
}
