/*
 * Surviveler entity package
 * buildings
 */
package entities

import (
	"server/game"
	"server/math"
	"time"
)

// TODO: those are const hard-coded for now, but have to be loaded from
// resources ideally
const (
	BuildingTotalHitPoints = 100
	RequiredBuildPower     = 50
)

// BuildingBase is a base containing the required fields for every building
type BuildingBase struct {
	totalHP      uint16 // total hit points
	curHP        uint16 // current hit points
	requiredBP   uint16 // required build power to finish construction
	curBP        uint16 // current build power induced in the construction
	id           uint32
	pos          math.Vec2
	buildingType game.EntityType
}

func (bb *BuildingBase) Type() game.EntityType {
	return bb.buildingType
}

func (bb *BuildingBase) Id() uint32 {
	return bb.id
}

func (bb *BuildingBase) SetId(id uint32) {
	bb.id = id
}

func (bb *BuildingBase) Position() math.Vec2 {
	return bb.pos
}

func (bb *BuildingBase) State() game.EntityState {
	// nothing, builds have no state, at least for now!
	return game.EntityState{}
}

type BuildingUpdater interface {
	Update(dt time.Duration)
}

/*
 * BasicBuilding is basic generic building.
 *
 * It will be replaced by different implementations, turrets, barricades.
 * It implements the Building interface.
 */
type BasicBuilding struct {
	BuildingBase
}

func NewBasicBuilding() *BasicBuilding {
	return &BasicBuilding{
		BuildingBase{
			totalHP:      BuildingTotalHitPoints,
			curHP:        BuildingTotalHitPoints,
			requiredBP:   RequiredBuildPower,
			curBP:        0,
			buildingType: 0,
		},
	}
}

func (bb *BasicBuilding) Update(dt time.Duration) {
}

// Induce a given quantity of build power into the building construction
func (bb *BasicBuilding) InduceBuildPower(bp uint16) {
	bb.curBP += bp
}

func (bb *BasicBuilding) IsBuilt() bool {
	return bb.curBP >= bb.requiredBP
}
