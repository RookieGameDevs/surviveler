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

type Object struct {
	id         uint32
	pos        math.Vec2
	objectType game.EntityType
	operatedBy game.Entity
}

/*
 * NewObject creates a new object and set its initial position
 */
func NewObject(g game.Game, gamestate game.GameState, pos math.Vec2, objectType game.EntityType) *Object {
	obj := new(Object)
	obj.pos = pos
	obj.objectType = objectType
	obj.id = game.InvalidId
	obj.operatedBy = nil

	return obj
}

func (obj *Object) Id() uint32 {
	return obj.id
}

func (obj *Object) SetId(id uint32) {
	obj.id = id
}

func (obj *Object) Type() game.EntityType {
	return obj.objectType
}

func (obj *Object) State() game.EntityState {
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

func (obj *Object) Position() math.Vec2 {
	return obj.pos
}

func (obj *Object) Update(dt time.Duration) {
	// Add code here
}

func (obj *Object) DealDamage(dmg float64) bool {
	// NOTE: no damage to clickable objects
	return false
}

func (obj *Object) BoundingBox() math.BoundingBox {
	x, y := obj.pos.Elem()
	return math.NewBoundingBox(x-0.25, x+0.25, y-0.25, y+0.25)
}

func (obj *Object) OperatedBy() game.Entity {
	return obj.operatedBy
}

func (obj *Object) Operate(ent game.Entity) (res bool) {
	res = true
	if obj.operatedBy != nil {
		res = false
	} else {
		obj.operatedBy = ent
	}
	return
}
