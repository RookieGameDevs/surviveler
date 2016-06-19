/*
 * Surviveler entity package
 * zombie
 */
package entities

import (
	"server/game"
	"server/game/components"
	"server/math"
	"time"
)

const (
	lookingState = iota
	walkingState
	runningState
	attackingState
)

const (
	zombieSpeed = 5.0
)

type Zombie struct {
	curState int // current state
	components.Movable
}

func NewZombie(pos math.Vec2) game.Entity {
	return &Zombie{
		curState: lookingState,
		Movable: components.Movable{
			Speed: zombieSpeed,
			Pos:   pos,
		},
	}
}

func (z *Zombie) Update(dt time.Duration) {
	switch z.curState {
	case lookingState:
		// TODO
	case walkingState:
		// TODO
	case runningState:
		// TODO
	case attackingState:
		// TODO
	}
}

func (z *Zombie) GetPosition() math.Vec2 {
	return z.Movable.Pos
}

func (z *Zombie) GetState() game.EntityState {
	// first, compile the data depending on current action
	var actionData interface{}
	var actionType game.ActionType

	switch z.curState {
	case lookingState:
	case attackingState:
		actionData = game.IdleActionData{}
		actionType = game.IdleAction

	case walkingState:
	case runningState:
		moveActionData := game.MoveActionData{
			Speed: z.Speed,
			Path:  z.Movable.GetPath(maxWaypointsToSend),
		}
		actionData = moveActionData
	}

	return game.EntityState{
		Type:       game.ZombieEntity,
		Xpos:       float32(z.Pos[0]),
		Ypos:       float32(z.Pos[1]),
		ActionType: actionType,
		Action:     actionData,
	}
}
