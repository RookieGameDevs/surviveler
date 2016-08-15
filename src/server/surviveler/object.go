/*
 * Surviveler package
 * object entities
 */
package surviveler

import (
	"server/game"
	"server/math"
	"time"
)

const (
	// FIXME: take us from resources!
	HealingFrequency = 500 * time.Millisecond
	HealingDistance  = 1.5 // healing distance for the coffee machine
	HealingPower     = 5   // healing power per tick
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
	cm := new(CoffeeMachine)
	cm.pos = pos
	cm.objectType = objectType
	cm.id = game.InvalidID
	cm.operatedBy = nil
	cm.g = g
	cm.gamestate = g.State()

	return cm
}

func (cm *CoffeeMachine) Id() uint32 {
	return cm.id
}

func (cm *CoffeeMachine) SetId(id uint32) {
	cm.id = id
}

func (cm *CoffeeMachine) Type() game.EntityType {
	return cm.objectType
}

func (cm *CoffeeMachine) State() game.EntityState {
	var operatedById uint32
	if cm.operatedBy == nil {
		operatedById = game.InvalidID
	} else {
		operatedById = cm.operatedBy.Id()
	}
	return game.ObjectState{
		Type:       cm.objectType,
		Xpos:       float32(cm.pos[0]),
		Ypos:       float32(cm.pos[1]),
		OperatedBy: operatedById,
	}
}

func (cm *CoffeeMachine) Position() math.Vec2 {
	return cm.pos
}

func (cm *CoffeeMachine) Update(dt time.Duration) {
	if cm.operatedBy != nil {
		dist := cm.operatedBy.Position().Sub(cm.pos).Len()
		if dist > HealingDistance {
			cm.operatedBy = nil
		} else {
			if time.Since(cm.lastHeal) > HealingFrequency {
				cm.operatedBy.HealDamage(HealingPower)
				cm.lastHeal = time.Now()
			}
		}
	}
}

func (cm *CoffeeMachine) DealDamage(dmg float64) bool {
	// NOTE: no damage to clickable objects
	return false
}

func (cm *CoffeeMachine) HealDamage(dmg float64) bool {
	// NOTE: no damage to clickable objects
	return true
}

func (cm *CoffeeMachine) BoundingBox() math.BoundingBox {
	x, y := cm.pos.Elem()
	return math.NewBoundingBox(x-0.25, x+0.25, y-0.25, y+0.25)
}

func (cm *CoffeeMachine) OperatedBy() game.Entity {
	return cm.operatedBy
}

func (cm *CoffeeMachine) Operate(ent game.Entity) (res bool) {
	res = true
	if cm.operatedBy == nil {
		cm.operatedBy = ent
		cm.lastHeal = time.Time{}
	} else {
		res = false
	}
	return
}
