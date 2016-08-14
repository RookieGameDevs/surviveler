/*
 * Surviveler entity package
 * player
 */
package entities

import (
	"server/events"
	"server/game"
	"server/game/actions"
	"server/math"
	"time"

	log "github.com/Sirupsen/logrus"
)

// player private action types
const (
	BuildPowerInductionPeriod = time.Second
	PlayerAttackDistance      = 1
	AttackPeriod              = 500 * time.Millisecond
	PathFindPeriod            = time.Second
)

/*
 * Player represents an entity that is controlled by a physical player. It
 * implements the Entity interface.
 */
type Player struct {
	id              uint32
	entityType      game.EntityType // player type
	actions         actions.Stack   // action stack
	lastBPinduced   time.Time       // time of last initiated BP induction
	lastAttack      time.Time       // time of last attack
	lastPathFind    time.Time       // time of last path find
	lastCoffeeDrink time.Time       // time of last coffee drink
	curBuilding     game.Building   // building in construction
	target          game.Entity
	curObject       game.Object
	g               game.Game
	gamestate       game.GameState
	world           *game.World
	buildPower      uint16
	combatPower     uint16
	totalHP         float64
	curHP           float64
	posDirty        bool
	*Movable
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(g game.Game, spawn math.Vec2, entityType game.EntityType,
	speed, totalHP float64, buildPower, combatPower uint16) *Player {
	p := &Player{
		entityType:  entityType,
		buildPower:  buildPower,
		combatPower: combatPower,
		totalHP:     totalHP,
		curHP:       totalHP,
		g:           g,
		gamestate:   g.State(),
		world:       g.State().World(),
		id:          game.InvalidID,
		actions:     *actions.NewStack(),
		Movable:     NewMovable(spawn, speed),
	}
	// place an idle action as the bottommost item of the action stack item.
	// This should never be removed as the player should remain idle if he
	// has nothing better to do
	p.actions.Push(actions.New(actions.IdleId, actions.Idle{}))
	return p
}

/*
 * Update updates the local state of the player
 */
func (p *Player) Update(dt time.Duration) {
	p.posDirty = false
	// peek the topmost stack action
	if action, exist := p.actions.Peek(); exist {
		switch action.Type {

		case actions.MoveId:

			p.onMoveAction(dt)

		case actions.BuildId, actions.RepairId:

			// build and repair actions actually end up being the same
			p.induceBuildPower()

		case actions.DrinkCoffeeId:
			p.curObject.Operate(p)
			p.actions.Pop()

		case actions.AttackId:

			dist := p.target.Position().Sub(p.Pos).Len()
			if dist < PlayerAttackDistance {
				if time.Since(p.lastAttack) >= AttackPeriod {
					if !p.target.DealDamage(float64(p.combatPower)) {
						p.lastAttack = time.Now()
					} else {
						// pop current action to get ready for next update
						next := p.actions.Pop()
						log.WithField("action", next).Debug("next player action")
					}
				}
			} else {
				p.posDirty = p.Movable.Move(dt)
				if time.Since(p.lastPathFind) > PathFindPeriod {
					p.findPath(p.target.Position())
				}
			}
		}
	}

	if p.posDirty {
		// update entity position only if needed
		p.gamestate.World().UpdateEntity(p)
		p.posDirty = true
	}
}

func (p *Player) onMoveAction(dt time.Duration) {
	// check if moving would create a collision
	nextPos := p.Movable.ComputeMove(p.Pos, dt)
	nextBB := math.NewBoundingBoxFromCircle(nextPos, 0.5)
	colliding := p.world.AABBSpatialQuery(nextBB)

	var curActionEnded bool

	// by design moving action can't be the last one
	nextAction := p.actions.PeekN(2)[1]

	colliding.Each(func(e game.Entity) bool {

		if e == p {
			// it's just me... pass
			return true
		}

		switch nextAction.Type {
		case actions.BuildId, actions.RepairId:
			if e == p.curBuilding {
				log.WithField("ent", e).Debug("collision with target building")
				// we are colliding with the building we wanna build/repair
				// current action has terminated
				p.actions.Pop()
				// do not check for other collisions
				curActionEnded = true
				return false
			}
		}
		return true
	})

	if !curActionEnded {

		// perform the actual move
		p.posDirty = p.Movable.Move(dt)
		if p.Movable.HasReachedDestination() {
			// pop current action to get ready for next update
			next := p.actions.Pop()
			log.WithField("action", next).Debug("next player action")
		}
	}
	return
}

func (p *Player) induceBuildPower() {
	bid := p.curBuilding.Id()
	if ent := p.gamestate.Entity(bid); ent == nil {
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
	p.Movable.SetPath(path)
}

/*
 * Move sets the player current action as 'moving' and define its macro-path.
 *
 * The player action stack is emptied, effectively cancelling any previous
 * player action, and defines its macro path.
 */
func (p *Player) Move(path math.Path) {
	// empty action stack, this cancel any current action(s)
	p.emptyActions()
	p.actions.Push(actions.New(actions.MoveId, struct{}{}))
	p.SetPath(path)
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
		actionData interface{}     // action data to be sent
		actionType actions.Type    //
		curAction  *actions.Action // action action from the stack
	)

	curAction, _ = p.actions.Peek()
	actionType = curAction.Type
	switch curAction.Type {
	case actions.MoveId:
		actionData = actions.Move{Speed: p.Speed}
	case actions.BuildId:
		actionData = actions.Build{}
	case actions.RepairId:
		actionData = actions.Repair{}
	case actions.IdleId:
		actionType = actions.IdleId
		actionData = actions.Idle{}
	case actions.AttackId:
		dist := p.target.Position().Sub(p.Pos).Len()
		if dist > PlayerAttackDistance {
			actionType = actions.MoveId
			actionData = actions.Move{Speed: p.Speed}
		} else {
			actionData = actions.Attack{TargetID: p.target.Id()}
			actionType = actions.AttackId
		}
	case actions.DrinkCoffeeId:
		actionType = actions.IdleId
		actionData = actions.Idle{}
	}

	return game.MobileEntityState{
		Type:         p.entityType,
		Xpos:         float32(p.Pos[0]),
		Ypos:         float32(p.Pos[1]),
		CurHitPoints: uint16(p.curHP),
		ActionType:   actionType,
		Action:       actionData,
	}
}

/*
 * Build sets the player as 'moving' and defines its macro-path, taking him to
 * the newly created building.
 *
 * The player action stack is emptied, effectively cancelling any previous
 * player action, and replaced with a 'move' action on top of a 'build'
 * action, that will immediately start once the player will be in contact
 * with the target building
 */
func (p *Player) Build(b game.Building, path math.Path) {
	// empty action stack, this cancel any current action(s)
	p.emptyActions()
	// fill the player action stack
	p.actions.Push(actions.New(actions.BuildId, actions.Build{}))
	p.actions.Push(actions.New(actions.MoveId, struct{}{}))
	p.curBuilding = b
	p.lastBPinduced = time.Time{}
	p.SetPath(path)
}

/*
 * Repair sets the player as 'moving' and defines its macro-path, taking him to
 * the building to repair.
 *
 * The player action stack is emptied, effectively cancelling any previous
 * player action, and replaced with a 'move' action on top of a 'repair'
 * action, that will immediately start once the player will be in contact
 * with the target building
 */
func (p *Player) Repair(b game.Building, path math.Path) {
	// empty action stack, this cancel any current action(s)
	p.emptyActions()
	// fill the player action stack
	p.actions.Push(actions.New(actions.BuildId, actions.Build{}))
	p.actions.Push(actions.New(actions.MoveId, struct{}{}))
	p.curBuilding = b
	p.lastBPinduced = time.Time{}
	p.SetPath(path)
}

func (p *Player) findPath(dst math.Vec2) {
	log.Debug("Player.findPath: directly search for a path")
	// directly search for path
	path, _, found := p.g.Pathfinder().FindPath(p.Position(), dst)
	if found == false {
		return
	}
	// set the path if found
	p.Movable.SetPath(path)
	p.lastPathFind = time.Now()
}

func (p *Player) Attack(e game.Entity) {
	log.Debug("Player.Attack")

	// directly search for path
	p.findPath(e.Position())
	p.lastAttack = time.Time{}

	// setup the actions in the stack
	p.emptyActions()
	p.actions.Push(actions.New(actions.AttackId, actions.Attack{}))
	p.target = e

}

/*
 * Operate sets the player as 'moving' and defines its macro-path, taking him to
 * the interactive object to operate.
 *
 * The player action stack is emptied, effectively cancelling any previous
 * player action, and replaced with a 'move' action on top of an 'operate'
 * action, that will immediately start once the player will be in contact
 * with the target interactive object.
 */
func (p *Player) Operate(o game.Object, path math.Path) {
	// empty action stack, this cancel any current action(s)
	p.emptyActions()

	var action *actions.Action

	switch o.Type() {
	case game.CoffeeMachineObject:
		action = actions.New(actions.DrinkCoffeeId, actions.DrinkCoffee{})
		p.lastCoffeeDrink = time.Time{}
	default:
		log.WithField("type", o.Type).Error("Player.Operate not implemented for this type of game object")
		return
	}

	// fill the player action stack
	p.actions.Push(action)
	p.actions.Push(actions.New(actions.MoveId, struct{}{}))
	p.curObject = o
	p.SetPath(path)
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

func (p *Player) DealDamage(damage float64) (dead bool) {
	if damage >= p.curHP {
		p.curHP = 0
		p.g.PostEvent(events.NewEvent(
			events.PlayerDeathId,
			events.PlayerDeath{Id: p.id}))
		dead = true
	} else {
		p.curHP -= damage
	}
	return
}

func (p *Player) HealDamage(damage float64) (healthy bool) {
	if damage+p.curHP >= p.totalHP {
		p.curHP = p.totalHP
		healthy = true
	} else {
		p.curHP += damage
	}
	return
}
