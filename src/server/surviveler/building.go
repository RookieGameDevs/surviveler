/*
 * Surviveler game package
 * buildings
 */
package surviveler

import (
	"server/events"
	"time"

	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/gogeo/f32/d2"
)

/*
 * BuildingBase is a base containing the required fields for every building
 *
 * It also embeds the common buiding features through methods like induceBuildPower,
 * etc.
 */
type BuildingBase struct {
	totalHP      float32 // total hit points
	curHP        float32 // current hit points
	requiredBP   uint16  // required build power to finish construction
	curBP        uint16  // build power already induced into the construction
	id           uint32
	g            *Game
	pos          d2.Vec2
	buildingType EntityType
	isBuilt      bool
}

func (bb *BuildingBase) Type() EntityType {
	return bb.buildingType
}

func (bb *BuildingBase) Id() uint32 {
	return bb.id
}

func (bb *BuildingBase) SetId(id uint32) {
	bb.id = id
}

func (bb *BuildingBase) Position() d2.Vec2 {
	return bb.pos
}

func (bb *BuildingBase) Rectangle() d2.Rectangle {
	x, y := bb.pos.X(), bb.pos.Y()
	return d2.Rect(x-0.25, y-0.25, x+0.25, y+0.25)
}

func (bb *BuildingBase) State() EntityState {
	return BuildingState{
		Type:         bb.buildingType,
		Xpos:         float32(bb.pos[0]),
		Ypos:         float32(bb.pos[1]),
		CurHitPoints: uint16(bb.curHP),
		Completed:    bb.isBuilt,
	}
}

func (bb *BuildingBase) DealDamage(damage float32) (dead bool) {
	if damage >= bb.curHP {
		bb.curHP = 0
		bb.g.PostEvent(events.NewEvent(
			events.BuildingDestroyId,
			events.BuildingDestroy{Id: bb.id}))
		dead = true
	} else {
		bb.curHP -= damage
	}
	return
}

func (bb *BuildingBase) HealDamage(damage float32) (healthy bool) {
	healthy = true
	return
}

func (bb *BuildingBase) addBuildPower(bp uint16) {
	if !bb.isBuilt {
		bb.curBP += bp
		bb.curHP = bb.totalHP * (float32(bb.curBP) / float32(bb.requiredBP))
		if bb.curBP >= bb.requiredBP {
			bb.isBuilt = true
			bb.curHP = bb.totalHP
			bb.curBP = bb.requiredBP
		}
		log.WithFields(log.Fields{
			"curHP": uint16(bb.curHP), "totHP": uint16(bb.totalHP),
			"curBP": bb.curBP, "reqBP": bb.requiredBP,
		}).Debug("Receiving Build Power")
	}
}

type BuildingUpdater interface {
	Update(dt time.Duration)
}

/*
 * Barricade is a simple barricade building
 *
 * It implements the Building interface
 */
type Barricade struct {
	BuildingBase
}

/*
 * NewBarricade creates a new barricade
 */
func NewBarricade(g *Game, pos d2.Vec2, totHP, reqBP uint16) *MgTurret {
	return &MgTurret{
		BuildingBase{
			id:           InvalidID,
			g:            g,
			pos:          pos,
			totalHP:      float32(totHP),
			curHP:        1,
			requiredBP:   reqBP,
			curBP:        0,
			buildingType: BarricadeBuilding,
		},
	}
}

func (mg *Barricade) Update(dt time.Duration) {
}

/*
 * AddBuildPower adds a given quantity of build power into the building.
 *
 * Build Power is induced by construction or reparation.
 */
func (mg *Barricade) AddBuildPower(bp uint16) {
	mg.addBuildPower(bp)
}

/*
 * IsBuilt indicates if the building is totally constructed.
 *
 * For the case of a building with shooting ability (eg a turret), this
 * implies the building is active and can shoot
 */
func (mg *Barricade) IsBuilt() bool {
	return mg.isBuilt
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
func NewMgTurret(g *Game, pos d2.Vec2, totHP, reqBP uint16) *MgTurret {
	return &MgTurret{
		BuildingBase{
			id:           InvalidID,
			g:            g,
			pos:          pos,
			totalHP:      float32(totHP),
			curHP:        1,
			requiredBP:   reqBP,
			curBP:        0,
			buildingType: MgTurretBuilding,
		},
	}
}

func (mg *MgTurret) Update(dt time.Duration) {
}

/*
 * AddBuildPower adds a given quantity of build power into the building.
 *
 * Build Power is induced by construction or reparation.
 */
func (mg *MgTurret) AddBuildPower(bp uint16) {
	mg.addBuildPower(bp)
}

/*
 * IsBuilt indicates if the building is totally constructed.
 *
 * For the case of a building with shooting ability (eg a turret), this
 * implies the building is active and can shoot
 */
func (mg *MgTurret) IsBuilt() bool {
	return mg.isBuilt
}
