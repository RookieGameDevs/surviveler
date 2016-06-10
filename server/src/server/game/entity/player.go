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
	curAction ActionType // current action
	MovableEntity
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(spawn math.Vec2, speed float32) *Player {
	p := new(Player)
	p.Speed = speed
	p.Pos = spawn
	p.curAction = IdleAction
	return p
}

/*
 * Update updates the local state of the player
 */
func (p *Player) Update(dt time.Duration) {
	if p.curAction != IdleAction {
		// update position on the player path
		pathLength := len(p.curPath)
		if pathLength > 0 {
			// get sub-destination (current path segment)
			subDst := p.curPath[p.curPathIdx]

			// compute translation vector
			moveVec := subDst.Sub(p.Pos).Normalize()
			p.Pos = p.Pos.Add(moveVec.Mul(float32(p.Speed * float32(dt.Seconds()))))

			if math.Abs(subDst[0]-p.Pos[0]) <= 0.01 &&
				math.Abs(subDst[1]-p.Pos[1]) <= 0.01 {
				// reached current sub-destination
				p.curPathIdx--
				p.Pos = subDst

				switch {
				case p.curPathIdx < 0:
					// this was the last path segment
					if p.curAction == MovingAction {
						// come back to Idle if nothing better to do...
						p.curAction = IdleAction
					}
				}
			}
		}
	}
}

/*
 * SetPath defines the path that the player should follow
 */
func (p *Player) SetPath(path []math.Vec2) {
	p.curPath = path
	p.curAction = MovingAction
	// the tail element of that path slice represents the starting point
	// it's also the position the player is already located, so we don't
	// want to send this position to the client
	p.curPathIdx = len(path) - 2
}

func (p *Player) GetState() EntityState {
	// first, compile the data depending on current action
	var actionData interface{}

	switch p.curAction {
	case IdleAction:
		actionData = IdleActionData{}

	case MovingAction:
		dst := p.curPath[p.curPathIdx]
		actionData = MoveActionData{
			Speed: p.Speed,
			Xpos:  dst[0],
			Ypos:  dst[1],
		}
	}
	return EntityState{
		Xpos:       p.Pos[0],
		Ypos:       p.Pos[1],
		ActionType: p.curAction,
		Action:     actionData,
	}
}
