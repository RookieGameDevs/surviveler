/*
 * Surviveler entity package
 * zombie
 */
package entities

import (
	"server/game"
	"server/game/components"
	"server/game/events"
	"server/math"
	"time"
)

/*
 * Possible zombie AI states.
 */
const (
	lookingState = iota
	walkingState
	runningState
	attackingState
)

// TODO: all of those values should be taken from the zombie resource
const (
	zombieLookingInterval    = 1 * time.Second
	zombieRunLookingInterval = 200 * time.Millisecond
	zombieDamageInterval     = 500 * time.Millisecond
	zombieWalkSpeed          = 1.0
	zombieRunSpeed           = 4.0
	rageDistance             = 4.0
	attackDistance           = 1.0
)

type Zombie struct {
	id          uint32
	g           game.Game
	curState    int // current state
	combatPower uint8
	runSpeed    float64
	walkSpeed   float64
	totalHP     float64
	curHP       float64
	timeAcc     time.Duration
	target      game.Entity
	world       *game.World
	components.Movable
}

func NewZombie(g game.Game, pos math.Vec2, walkSpeed float64, combatPower uint8, totalHP float64) *Zombie {
	z := &Zombie{
		id:          game.InvalidId,
		g:           g,
		curState:    lookingState,
		walkSpeed:   walkSpeed,
		totalHP:     totalHP,
		curHP:       totalHP,
		combatPower: combatPower,
		world:       g.State().World(),
		Movable: components.Movable{
			Speed: walkSpeed,
			Pos:   pos,
		},
	}
	return &z
}

func (z *Zombie) Id() uint32 {
	return z.id
}

func (z *Zombie) SetId(id uint32) {
	z.id = id
}

func (z *Zombie) findPathToTarget() (math.Path, bool) {
	path, _, found := z.g.Pathfinder().FindPath(z.Pos, z.target.Position())
	return path, found
}

func (z *Zombie) look(dt time.Duration) (state int) {
	state = z.curState

	ent, dist := z.findTarget()
	if ent != nil {
		// update the target
		z.target = ent

		path, found := z.findPathToTarget()
		if found == false {
			return
		}
		z.SetPath(path)

		// update the state
		if dist < rageDistance {
			state = runningState
		} else {
			state = walkingState
		}
	}
	return
}

func (z *Zombie) walk(dt time.Duration) (state int) {
	state = z.curState

	dist := z.target.Position().Sub(z.Pos).Len()
	if dist < rageDistance {
		state = runningState
		return
	}

	if z.timeAcc >= zombieLookingInterval {
		z.timeAcc -= zombieLookingInterval
		state = lookingState
		return
	}

	z.Speed = z.walkSpeed
	if z.Movable.Move(dt) {
		z.world.UpdateEntity(z)
	}

	return
}

func (z *Zombie) run(dt time.Duration) (state int) {
	state = z.curState

	if z.timeAcc >= zombieRunLookingInterval {
		z.timeAcc -= zombieRunLookingInterval

		path, found := z.findPathToTarget()
		if found == false {
			state = lookingState
			return
		}
		z.SetPath(path)
	}

	z.Speed = zombieRunSpeed
	if z.Movable.Move(dt) {
		z.world.UpdateEntity(z)
	}

	if z.target.Position().Sub(z.Pos).Len() <= attackDistance {
		state = attackingState
	}

	return
}

func (z *Zombie) attack(dt time.Duration) (state int) {
	state = z.curState

	if z.target.Position().Sub(z.Pos).Len() > attackDistance {
		state = runningState
		return
	}

	if z.timeAcc >= zombieDamageInterval {
		z.timeAcc -= zombieDamageInterval
		if z.target.DealDamage(float64(z.combatPower)) {
			state = lookingState
		}
	}

	return
}

func (z *Zombie) Update(dt time.Duration) {
	z.timeAcc += dt

	// TODO: check target entity existance; fallback to lookingState in case it
	// doesn't

	stateMap := map[int]func(time.Duration) int{
		lookingState:   z.look,
		walkingState:   z.walk,
		runningState:   z.run,
		attackingState: z.attack,
	}

	nextState := stateMap[z.curState](dt)
	if nextState != z.curState {
		z.timeAcc = 0
		z.curState = nextState
	}
}

func (z *Zombie) Position() math.Vec2 {
	return z.Pos
}

func (z *Zombie) Type() game.EntityType {
	return game.ZombieEntity
}

func (z *Zombie) State() game.EntityState {
	// first, compile the data depending on current action
	var actionData interface{} = game.IdleActionData{}
	var actionType game.ActionType = game.IdleAction

	switch z.curState {
	case lookingState:
		fallthrough
	case attackingState:
		// TODO: we are doing nothing here.
	case walkingState:
		fallthrough
	case runningState:
		if !z.Movable.HasReachedDestination() {
			moveActionData := game.MoveActionData{
				Speed: z.Speed,
				Path:  z.Movable.NextWaypoints(),
			}
			actionType = game.MovingAction
			actionData = moveActionData
		}
	}

	return game.MobileEntityState{
		Type:         game.ZombieEntity,
		Xpos:         float32(z.Pos[0]),
		Ypos:         float32(z.Pos[1]),
		CurHitPoints: uint16(z.curHP),
		ActionType:   actionType,
		Action:       actionData,
	}
}

func (z *Zombie) findTarget() (game.Entity, float32) {
	ent, dist := z.g.State().NearestEntity(
		z.Pos,
		func(e game.Entity) bool {
			return e.Type() != game.ZombieEntity
		},
	)
	return ent, dist
}

func (z *Zombie) DealDamage(damage float64) (dead bool) {
	if damage >= z.curHP {
		z.curHP = 0
		z.g.PostEvent(events.NewEvent(
			events.ZombieDeath,
			events.ZombieDeathEvent{Id: z.id}))
		dead = true
	} else {
		z.curHP -= damage
	}
	return
}
