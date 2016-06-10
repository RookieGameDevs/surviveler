/*
 * Surviveler entity package
 * zombie
 */
package entity

import (
//"server/math"
//"time"
)

type ZombieType int

type Zombie struct {
	MovableEntity
	ZombieUpdater
}

func NewZombie(zu ZombieUpdater) *Zombie {
	return &Zombie{
		ZombieUpdater: zu,
	}
}

type ZombieUpdater interface {
	Updater
}

type ZombieWithDestination struct {
}

//func (z *Zombie) Update(dt time.Duration) {
//z.updater.Update(dt)
//}
