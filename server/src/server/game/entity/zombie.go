/*
 * Surviveler entity package
 * zombie
 */
package entity

import (
	"server/math"
	"time"
)

const (
	watchingState = iota
	roamingState
	chasingState
)

const (
	zombieSpeed = 5.0
)

type Zombie struct {
	curState int // current state
	Movable
}

func NewZombie(pos math.Vec2) *Zombie {
	return &Zombie{
		curState: watchingState,
		Movable: Movable{
			Speed: zombieSpeed,
			Pos:   pos,
		},
	}
}

func (z *Zombie) Update(dt time.Duration) {
	// TODO
}

func (z *Zombie) GetState() EntityState {
	// first, compile the data depending on current action
	var actionData interface{}
	var actionType ActionType

	switch z.curState {
	case watchingState:
		actionData = IdleActionData{}
		actionType = IdleAction

	case roamingState:
	case chasingState:
		from := z.curPathIdx
		to := math.IMin(from+maxWaypointsToSend, len(z.curPath))
		moveActionData := MoveActionData{
			Speed: z.Speed,
			Path:  make([]math.Vec2, to-from),
		}
		copy(moveActionData.Path, z.curPath[from:to])
		actionData = moveActionData
		actionType = MovingAction
	}

	return EntityState{
		Type:       ZombieEntity,
		Xpos:       float32(z.Pos[0]),
		Ypos:       float32(z.Pos[1]),
		ActionType: actionType,
		Action:     actionData,
	}
}
