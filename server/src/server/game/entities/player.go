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
	gs            game.GameState
	buildPower    uint16
	components.Movable
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(gs game.GameState, spawn math.Vec2, entityType game.EntityType,
	speed float64, buildPower uint16) *Player {
	p := new(Player)
	p.entityType = entityType
	p.Movable = components.Movable{
		Pos:   spawn,
		Speed: speed,
	}
	p.buildPower = buildPower
	p.gs = gs
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

			log.Debug("player is waiting for a path")

		case game.BuildingAction, game.RepairingAction:
			// building/repairing actually end up being the same
			p.induceBuildPower()
		}
	} else {
		// little consistency check...
		log.Panic("There should always be one action in player ActionStack...")
	}
}

func (p *Player) induceBuildPower() {
	bid := p.curBuilding.Id()
	if ent := p.gs.Entity(bid); ent == nil {
		// building doesn't exist anymore, cancel action
		p.curBuilding = nil
		p.actions.Pop()
		return
	}

	// induce build power by chunks of `player BP` per second
	if time.Since(p.lastBPinduced) > BuildPowerInductionPeriod {
		// period elapsed -> induce BP
		p.curBuilding.AddBuildPower(p.buildPower)
		p.lastBPinduced = time.Now()
	}

	if p.curBuilding.IsBuilt() {
		// building is built: pop current action
		p.curBuilding = nil
		p.actions.Pop()
		// zero time of last BP induced
		p.lastBPinduced = time.Time{}
	}
}

/*
 * SetPath defines the path that the player must follow.
 */
func (p *Player) SetPath(path math.Path) {
	log.Debug("Player.SetPath, setting path to movable")
	p.actions.Pop()
	p.Movable.SetPath(path)
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
	case game.RepairingAction:
		actionData = game.RepairActionData{}
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
 * Build makes the player initiates a build action
 *
 * It cancels any high-level actions the player may already be doing and set
 * the player as waiting for the calculated path to join the building point.
 * At destination, it immediately starts the construction until the building
 * is complete.
 */
func (p *Player) Build(b game.Building) {
	log.Debug("Player.Build")
	p.moveAndAction(game.BuildingAction, game.BuildActionData{})
	p.curBuilding = b
	p.lastBPinduced = time.Time{}
}

/*
 * Repair makes the player initiates a repair action
 *
 * It cancels any high-level actions the player may already be doing and set
 * the player as waiting for the calculated path to join the building point.
 * At destination, it immediately repairs the building until its completion.
 */
func (p *Player) Repair(b game.Building) {
	log.Debug("Player.Repair")
	p.moveAndAction(game.RepairingAction, game.RepairActionData{})
	p.curBuilding = b
	p.lastBPinduced = time.Time{}
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

/*
 * moveAndAction makes a player move until to reach a specified action point
 *
 * After this call, the player will be waiting for a path. When received, he
 * will be moving alongside the path. When reached the path destination, the
 * specified action will begin
 */
func (p *Player) moveAndAction(actionType game.ActionType, actionData interface{}) {
	// empty action stack, this cancel any current action(s)
	p.emptyActions()
	// fill the player action stack
	p.actions.Push(&game.Action{actionType, actionData})
	p.actions.Push(&game.Action{game.MovingAction, struct{}{}})
	p.actions.Push(&game.Action{WaitingForPathAction, struct{}{}})
}
