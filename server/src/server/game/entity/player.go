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
 * Number of waypoints to send in movement action payloads.
 */
const playerWaypointsToSend = 3

/*
 * Player represents an entity that is controlled by a physical player. It
 * implements the Entity interface.
 */
type Player struct {
	entityType EntityType // player type
	curAction  ActionType // current action
	MovableEntity
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(spawn math.Vec2, speed float64) *Player {
	p := new(Player)
	p.entityType = TypeTank
	p.Speed = speed
	p.Pos = spawn
	p.curAction = IdleAction
	return p
}

/*
 * Update updates the local state of the player
 */
func (p *Player) Update(dt time.Duration) {
	if p.curAction == MovingAction {
		p.MovableEntity.Update(dt)
		if p.MovableEntity.hasReachedDestination {
			// come back to Idle if nothing better to do...
			p.curAction = IdleAction
		}
	}
}

func (p *Player) SetPath(path math.Path) {
	p.curAction = MovingAction
	p.MovableEntity.SetPath(path)
}

func (p *Player) GetState() EntityState {
	// first, compile the data depending on current action
	var actionData interface{}

	switch p.curAction {
	case IdleAction:
		actionData = IdleActionData{}

	case MovingAction:
		from := p.curPathIdx
		to := math.IMin(from + waypointsToSend, len(p.curPath))
		moveActionData := MoveActionData{
			Speed: p.Speed,
			Waypoints: make([]math.Vec2, to - from),
		}
		copy(moveActionData.Waypoints, p.curPath[from:to])
		actionData = moveActionData
	}
	return EntityState{
		Type:       p.GetType(),
		Xpos:       float32(p.Pos[0]),
		Ypos:       float32(p.Pos[1]),
		ActionType: p.curAction,
		Action:     actionData,
	}
}

func (p *Player) GetType() EntityType {
	return p.entityType
}
