/*
 * Surviveler package
 * object entities
 */
package surviveler

import (
	"time"

	"github.com/aurelien-rainone/gogeo/f32/d2"
)

type Computer struct {
	id         uint32
	pos        d2.Vec2
	objectType EntityType
	operatedBy Entity
	g          *Game
	gamestate  *GameState
}

/*
 * Computer creates a new object and set its initial position
 */
func NewComputer(g *Game, pos d2.Vec2, objectType EntityType) *Computer {
	cm := new(Computer)
	cm.pos = pos
	cm.objectType = objectType
	cm.id = InvalidID
	cm.operatedBy = nil
	cm.g = g
	cm.gamestate = g.State()

	return cm
}

func (cm *Computer) Id() uint32 {
	return cm.id
}

func (cm *Computer) SetId(id uint32) {
	cm.id = id
}

func (cm *Computer) Type() EntityType {
	return cm.objectType
}

func (cm *Computer) State() EntityState {
	var operatorID uint32
	if cm.operatedBy == nil {
		operatorID = InvalidID
	} else {
		operatorID = cm.operatedBy.Id()
	}
	return ObjectState{
		Type:       cm.objectType,
		Xpos:       float32(cm.pos[0]),
		Ypos:       float32(cm.pos[1]),
		OperatedBy: operatorID,
	}
}

func (cm *Computer) Position() d2.Vec2 {
	return cm.pos
}

func (cm *Computer) Update(dt time.Duration) {
	// NOTE: nothing to do
}

func (cm *Computer) DealDamage(dmg float32) bool {
	// NOTE: no damage to clickable objects
	return false
}

func (cm *Computer) HealDamage(dmg float32) bool {
	// NOTE: no damage to clickable objects
	return true
}

func (cm *Computer) Rectangle() d2.Rectangle {
	x, y := cm.pos[0], cm.pos[1]
	return d2.Rect(x-0.25, y-0.25, x+0.25, y+0.25)
}

func (cm *Computer) OperatedBy() Entity {
	return cm.operatedBy
}

func (cm *Computer) Operate(ent Entity) (res bool) {
	res = true
	if cm.operatedBy == nil {
		cm.operatedBy = ent
	} else {
		res = false
	}
	return
}
