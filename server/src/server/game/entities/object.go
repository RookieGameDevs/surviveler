/*
 * Surviveler entity package
 * object
 */
package entities

import (
	"server/game"
	"server/math"
	"time"
)

const (
	// FIXME: take us from resources!
	HealingFrequency = 500 * time.Millisecond
	HealingDistance  = 1.5 // healing distance for the coffee machine
	HealingPower     = 10  // healing power per tick
)

type CoffeeMachine struct {
	id         uint32
	pos        math.Vec2
	objectType game.EntityType
	operatedBy game.Entity
	lastHeal   time.Time
	g          game.Game
	gamestate  game.GameState
}

/*
 * NewCoffeeMachine creates a new object and set its initial position
 */
func NewCoffeeMachine(g game.Game, pos math.Vec2, objectType game.EntityType) *CoffeeMachine {
	obj := new(CoffeeMachine)
	obj.pos = pos
	obj.objectType = objectType
	obj.id = game.InvalidId
	obj.operatedBy = nil
	obj.g = g
	obj.gamestate = g.State()

	return obj
}

func (obj *CoffeeMachine) Id() uint32 {
	return obj.id
}

func (obj *CoffeeMachine) SetId(id uint32) {
	obj.id = id
}

func (obj *CoffeeMachine) Type() game.EntityType {
	return obj.objectType
}

func (obj *CoffeeMachine) State() game.EntityState {
	var operatedById uint32
	if obj.operatedBy == nil {
		operatedById = game.InvalidId
	} else {
		operatedById = obj.operatedBy.Id()
	}
	return game.ObjectState{
		Type:       obj.objectType,
		Xpos:       float32(obj.pos[0]),
		Ypos:       float32(obj.pos[1]),
		OperatedBy: operatedById,
	}
}

func (obj *CoffeeMachine) Position() math.Vec2 {
	return obj.pos
}

func (obj *CoffeeMachine) Update(dt time.Duration) {
	if obj.operatedBy != nil {
		dist := obj.operatedBy.Position().Sub(obj.pos).Len()
		if dist > HealingDistance {
			obj.operatedBy = nil
		} else {
			if time.Since(obj.lastHeal) > HealingFrequency {
				obj.operatedBy.HealDamage(HealingPower)
				obj.lastHeal = time.Now()
			}
		}
	}
}

func (obj *CoffeeMachine) DealDamage(dmg float64) bool {
	// NOTE: no damage to clickable objects
	return false
}

func (obj *CoffeeMachine) HealDamage(dmg float64) bool {
	// NOTE: no damage to clickable objects
	return true
}

func (obj *CoffeeMachine) BoundingBox() math.BoundingBox {
	x, y := obj.pos.Elem()
	return math.NewBoundingBox(x-0.25, x+0.25, y-0.25, y+0.25)
}

func (obj *CoffeeMachine) OperatedBy() game.Entity {
	return obj.operatedBy
}

func (obj *CoffeeMachine) Operate(ent game.Entity) (res bool) {
	res = true
	if obj.operatedBy == nil {
		obj.operatedBy = ent
		obj.lastHeal = time.Time{}
	} else {
		res = false
	}
	return
}
