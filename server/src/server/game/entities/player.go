/*
 * Surviveler entity package
 * player
 */
package entities

import (
	"server/game"
	"server/game/components"
	"server/math"
	"time"
)

/*
 * Number of waypoints to send in movement action payloads.
 */
const maxWaypointsToSend = 3

/*
 * Player represents an entity that is controlled by a physical player. It
 * implements the Entity interface.
 */
type Player struct {
	entityType game.EntityType // player type
	curAction  game.ActionType // current action
	components.Movable
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(spawn math.Vec2, speed float64, entityType game.EntityType) *Player {
	p := new(Player)
	p.entityType = entityType
	p.Speed = speed
	p.Pos = spawn
	p.curAction = game.IdleAction
	return p
}

/*
 * Update updates the local state of the player
 */
func (p *Player) Update(dt time.Duration) {
	if p.curAction == game.MovingAction {
		p.Movable.Update(dt)
		if p.Movable.HasReachedDestination() {
			// come back to Idle if nothing better to do...
			p.curAction = game.IdleAction
		}
	}
}

func (p *Player) SetPath(path math.Path) {
	p.curAction = game.MovingAction
	p.Movable.SetPath(path)
}

func (p *Player) GetPosition() math.Vec2 {
	return p.Movable.Pos
}

func (p *Player) GetType() game.EntityType {
	return p.entityType
}

func (p *Player) GetState() game.EntityState {
	// first, compile the data depending on current action
	var actionData interface{}

	switch p.curAction {
	case game.IdleAction:
		actionData = game.IdleActionData{}

	case game.MovingAction:
		moveActionData := game.MoveActionData{
			Speed: p.Speed,
			Path:  p.Movable.GetPath(maxWaypointsToSend),
		}
		actionData = moveActionData
	}
	return game.EntityState{
		Type:       p.entityType,
		Xpos:       float32(p.Pos[0]),
		Ypos:       float32(p.Pos[1]),
		ActionType: p.curAction,
		Action:     actionData,
	}
}

func (p *Player) Build() {
	fmt.Println("in player.build")
}
