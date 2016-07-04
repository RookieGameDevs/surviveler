/*
 * Surviveler entity package
 * buildings
 */
package entities

import (
	//"server/game"
	//"server/game/components"
	//"server/math"
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
	totalHP    uint16 // total hit points
	curHP      uint16 // current hit points
	requiredBP uint16 // required build power to finish construction
	curBP      uint16 // current build power induced in the construction
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
			totalHP:    BuildingTotalHitPoints,
			curHP:      BuildingTotalHitPoints,
			requiredBP: RequiredBuildPower,
			curBP:      0,
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
