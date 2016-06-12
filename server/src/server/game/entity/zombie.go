/*
 * Surviveler entity package
 * zombie
 */
package entity

import (
	"server/math"
	"time"
)

const ZombieWandererType uint32 = 1

type ZombieType int

type ZombieEntity interface {
	Updater
}

type Zombie struct {
	ZombieEntity Entity
	Type         uint32
}

func (z *Zombie) Update(dt time.Duration) {
	z.ZombieEntity.Update(dt)
}

func (z *Zombie) GetState() EntityState {
	return z.ZombieEntity.GetState()
}

type ZombieWandererEntity struct {
	curAction ActionType // current action
	MovableEntity
}

func NewZombieWanderer(spawn math.Vec2, path math.Path, speed float64) *Zombie {
	return &Zombie{
		ZombieEntity: NewZombieWandererEntity(spawn, path, speed),
		Type:         ZombieWandererType,
	}
}

func NewZombieWandererEntity(spawn math.Vec2, path math.Path, speed float64) *ZombieWandererEntity {
	z := new(ZombieWandererEntity)
	z.Speed = speed
	z.Pos = spawn
	z.curAction = MovingAction
	z.MovableEntity.SetPath(path)
	return z
}

func (z *ZombieWandererEntity) Update(dt time.Duration) {
	if z.curAction == MovingAction {
		z.MovableEntity.Update(dt)
		if z.MovableEntity.hasReachedDestination {
			// come back to Idle if nothing better to do...
			z.curAction = IdleAction
		}
	}
}

func (z *ZombieWandererEntity) GetState() EntityState {
	// first, compile the data depending on current action
	var actionData interface{}

	switch z.curAction {
	case IdleAction:
		actionData = IdleActionData{}

	case MovingAction:
		dst := z.curPath[z.curPathIdx]
		actionData = MoveActionData{
			Speed: float32(z.Speed),
			Xpos:  float32(dst[0]),
			Ypos:  float32(dst[1]),
		}
	}
	return EntityState{
		Xpos:       float32(z.Pos[0]),
		Ypos:       float32(z.Pos[1]),
		ActionType: z.curAction,
		Action:     actionData,
	}
}
