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
	WaitingForPathAction      = 1000 + iota
	PlayerBuildPower          = 3 // this is hard-coded for now, but will ideally be loaded from asset package
	BuildPowerInductionPeriod = time.Second
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
	id            uint32
	entityType    game.EntityType  // player type
	actions       game.ActionStack // action stack
	lastBPinduced time.Time        // time of last initiated BP induction
	curBuilding   game.Building    // building in construction
	g             game.Game
	components.Movable
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(g game.Game, spawn math.Vec2, speed float64, entityType game.EntityType) *Player {
	p := new(Player)
	p.entityType = entityType
	p.Speed = speed
	p.Pos = spawn
	p.g = g
	p.id = game.InvalidId
	p.curBuilding = nil

	// place an idle action as the bottommost item of the action stack item.
	// This should never be removed as the player should remain idle if he
	// has nothing better to do
	p.actions = *game.NewActionStack()
	p.actions.Push(&game.Action{game.IdleAction, game.IdleActionData{}})
	return p
}

/*
 * Update updates the local state of the player
 */
func (p *Player) Update(dt time.Duration) {
	// peek the topmost stack action
	if action, exist := p.actions.Peek(); exist {
		switch action.Type {
		case game.MovingAction:
			p.Movable.Update(dt)
			if p.Movable.HasReachedDestination() {
				// pop current action to get ready for next update
				next := p.actions.Pop()
				log.WithField("action", next).Debug("next player action")
			}

		case WaitingForPathAction:
			log.Debug("player is waiting for path action")

		case game.BuildingAction:

			if p.lastBPinduced.IsZero() {
				// we are starting to build, mark current time
				p.lastBPinduced = time.Now()
				log.WithField("building", p.curBuilding).
					Info("Starting building construction")

			} else {

				if time.Since(p.lastBPinduced) > BuildPowerInductionPeriod {
					// BP induction period elapsed -> transmit BP to building
					p.curBuilding.InduceBuildPower(PlayerBuildPower)
					p.lastBPinduced = time.Now()
					log.WithFields(log.Fields{
						"player":   p.id,
						"building": p.curBuilding.Id(),
					}).Debug("Inducing Build Power")
				}
				if p.curBuilding.IsBuilt() {
					log.WithField("building", p.curBuilding).
						Info("Player finished building construction")
					p.curBuilding = nil
					p.actions.Pop()
				}
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
	if action, exist := p.actions.Peek(); !exist {
		// check stack
		log.Panic("Player.actions stack should not be empty")
	} else if action.Type != WaitingForPathAction {
		// check stack topmost item
		log.WithField("action", action.Type).
			Panic("next action in Player.actions stack must be WaitingForPathAction")
	} else {
		log.Debug("Player.SetPath, setting path to movable")
		p.actions.Pop()
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
	log.Debug("Player.Move")
	p.emptyActions()
	p.actions.Push(&game.Action{game.MovingAction, struct{}{}})
	p.actions.Push(&game.Action{WaitingForPathAction, struct{}{}})
}

func (p *Player) Position() math.Vec2 {
	return p.Movable.Pos
}

func (p *Player) Type() game.EntityType {
	return p.entityType
}

func (p *Player) SetId(id uint32) {
	p.id = id
}

func (p *Player) Id() uint32 {
	return p.id
}

func (p *Player) State() game.EntityState {
	var (
		actionData interface{}  // action data to be sent
		curAction  *game.Action // action action from the stack
	)

	curAction, _ = p.actions.Peek()
	switch curAction.Type {
	case game.MovingAction:
		actionData = game.MoveActionData{
			Speed: p.Speed,
			Path:  p.Movable.Path(maxWaypointsToSend),
		}
	case game.BuildingAction:
		actionData = game.BuildActionData{}
	case game.IdleAction:
		actionData = game.IdleActionData{}
	}

	return game.MobileEntityState{
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

func (p *Player) Build(b game.Building) {
	log.Debug("Player.Build")
	// empty action stack, this cancel any current action(s)
	p.emptyActions()
	// fill the player action stack
	p.actions.Push(&game.Action{game.BuildingAction, struct{}{}})
	p.actions.Push(&game.Action{game.MovingAction, struct{}{}})
	p.actions.Push(&game.Action{WaitingForPathAction, struct{}{}})
	p.curBuilding = b
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
