/*
 * Surviveler entity package
 * player
 */
package entities

import (
	log "github.com/Sirupsen/logrus"
	"server/game"
	"server/game/components"
	"server/math"
	"time"
)

// player private action types
const (
	WaitingForPathAction = 1000 + iota
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
	id         uint32
	entityType game.EntityType  // player type
	actions    game.ActionStack // action stack
	components.Movable
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(id uint32, spawn math.Vec2, speed float64, entityType game.EntityType) *Player {
	p := new(Player)
	p.id = id
	p.entityType = entityType
	p.Speed = speed
	p.Pos = spawn

	// place an idle action as bottommost action stack item this should
	// never be removed as the player should remain idle when he has nothing
	// better to do
	p.actions = *game.NewActionStack()
	p.actions.Push(&game.Action{game.IdleAction, game.IdleActionData{}})
	return p
}

func (p *Player) GetId() uint32 {
	return p.id
}

/*
 * Update updates the local state of the player
 */
func (p *Player) Update(dt time.Duration) {
	// peek the topmost stack action
	if action, exist := p.actions.Peek(); exist {
		switch action.Type {
		case game.MovingAction:
			// the action data is not interesting as it should always
			p.Movable.Update(dt)
			if p.Movable.HasReachedDestination() {
				// pop current action to get ready for next update
				p.actions.Pop()
			}
		}
	} else {
		// little consistency check...
		log.Panic("There should always be one action in player ActionStack...")
	}
}

/*
 * SetPath defines the path that the player must follow.
 */
func (p *Player) SetPath(path math.Path) {
	// consistency check: we should be waiting for a path
	if action := p.actions.Pop(); action.Type != WaitingForPathAction {
		log.WithField("action", action.Type).
			Panic("calling player.SetPath while we are not waiting for a path")
	} else {
		p.Movable.SetPath(path)
	}
}

/*
 * Move makes the player initiates a move action
 *
 * It cancels any high-level actions the player may already be doing and set
 * the player as waiting for the calculated path
 */
func (p *Player) Move() {
	p.emptyActions()
	p.actions.Push(&game.Action{game.MovingAction, struct{}{}})
	p.actions.Push(&game.Action{WaitingForPathAction, struct{}{}})
}

func (p *Player) GetPosition() math.Vec2 {
	return p.Movable.Pos
}

func (p *Player) GetType() game.EntityType {
	return p.entityType
}

func (p *Player) GetState() game.EntityState {
	var (
		actionData interface{}  // action data to be sent
		curAction  *game.Action // action action from the stack
	)

	curAction, _ = p.actions.Peek()
	switch curAction.Type {
	case game.IdleAction:
		actionData = game.IdleActionData{}

	case game.MovingAction:
		actionData = game.MoveActionData{
			Speed: p.Speed,
			Path:  p.Movable.GetPath(maxWaypointsToSend),
		}
	}

	return game.EntityState{
		Type:       p.entityType,
		Xpos:       float32(p.Pos[0]),
		Ypos:       float32(p.Pos[1]),
		ActionType: curAction.Type,
		Action:     actionData,
	}
}

/*
 * Move makes the player initiates a build action
 *
 * It cancels any high-level actions the player may already be doing and set
 * the player as waiting for the calculated path to join the building point
 */

func (p *Player) Build(t uint8, pos math.Vec2) {
	p.emptyActions()
	p.actions.Push(&game.Action{game.BuildingAction, struct{}{}})
	p.actions.Push(&game.Action{game.MovingAction, struct{}{}})
	p.actions.Push(&game.Action{WaitingForPathAction, struct{}{}})
}

/*
 * emptyActions removes all the actions from the actions stack.
 *
 * It removes all actions but the last one: `IdleAction`.
 */
func (p *Player) emptyActions() {
	// empty the action stack, just let the bottommost (idle)
	for ; p.actions.Len() > 1; p.actions.Pop() {
	}
}
