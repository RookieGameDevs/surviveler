/*
 * Surviveler entity package
 * buildings
 */
package entities

import (
	log "github.com/Sirupsen/logrus"
	"server/game"
	"server/math"
	"time"
)

/*
 * BuildingBase is a base containing the required fields for every building
 *
 * It also embeds the common buiding features through methods like induceBuildPower,
 * etc.
 */
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

func (bb *BuildingBase) induceBuildPower(bp uint16) {
	if !bb.isBuilt {
		bb.curBP += bp
		bb.curHP = bb.totalHP * (float64(bb.curBP) / float64(bb.requiredBP))
		if bb.curBP >= bb.requiredBP {
			bb.isBuilt = true
			bb.curHP = bb.totalHP
			bb.curBP = bb.requiredBP
		}
		log.WithFields(log.Fields{
			"curHP": uint16(bb.curHP), "totHP": uint16(bb.totalHP),
			"curBP": bb.curBP, "reqBP": bb.requiredBP,
		}).Debug("Inducing Build Power")
	}
}

type BuildingUpdater interface {
	Update(dt time.Duration)
}

/*
 * MgTurret is a machine-gun turret building
 *
 * It implements the Building interface
 */
type MgTurret struct {
	BuildingBase
}

/*
 * NewMgTurret creates a new machine-gun turret
 */
func NewMgTurret(totHP, reqBP uint16) *MgTurret {
	return &MgTurret{
		BuildingBase{
			id:           game.InvalidId,
			totalHP:      float64(totHP),
			curHP:        1,
			requiredBP:   reqBP,
			curBP:        0,
			buildingType: game.MgTurretBuilding,
		},
	}
}

func (mg *MgTurret) Update(dt time.Duration) {
}

/*
 * Induce a given quantity of build power into the building construction
 */
func (mg *MgTurret) InduceBuildPower(bp uint16) {
	mg.induceBuildPower(bp)
}

func (mg *MgTurret) IsBuilt() bool {
	return mg.isBuilt
}
