/*
 * Entity abstractions.
 */
package game

import (
	gomath "math"
	"server/math"
	"time"
)

//go:generate go-gencon -type Entity -cont Set -name EntitySet

/*
 * Enumeration of possible entity types.
 */
type EntityType uint8

/*
 * Playable Entity type identifiers.
 */
const (
	TankEntity EntityType = iota
	ProgrammerEntity
	EngineerEntity
	ZombieEntity
)

/*
 * Building type identifiers.
 */
const (
	MgTurretBuilding EntityType = iota
)

const (
	InvalidId uint32 = gomath.MaxUint32
)

/*
 * Entity is the interface that represents stateful game objects
 */
type Entity interface {
	Id() uint32 // should return InvalidId if Id has not been assigned yet
	SetId(uint32)
	Type() EntityType
	State() EntityState
	Position() math.Vec2
	Update(dt time.Duration)
	DealDamage(float64) bool
	math.BoundingBoxer
}

/*
 * MobileEntity is an entity that accepts a path
 */
type MobileEntity interface {
	Entity
	SetPath(path math.Path)
}

/*
 * Building is the interface implemented by building objects.
 *
 * Buildings are entities and thus implement the Entity interface
 */
type Building interface {
	Entity

	// IsBuilt indicates if the building is totally constructed.
	//
	// For the case of a building with shooting ability (eg a turret), this
	// implies the building is active and can shoot
	IsBuilt() bool

	// AddBuildPower adds a given quantity of build power into the building.
	//
	// Build Power is induced by construction or reparation.
	AddBuildPower(bp uint16)
}

/*
 * EntityState represents a snapshot of an entity state
 */
type EntityState interface{}

/*
 * MobileEntityState represents a snapshot of a mobile entity
 */
type MobileEntityState struct {
	Type         EntityType
	Xpos         float32
	Ypos         float32
	CurHitPoints uint16
	ActionType   ActionType
	Action       interface{}
}

/*
 * BuildingState represents a snapshot of a building
 */
type BuildingState struct {
	Type         EntityType
	Xpos         float32
	Ypos         float32
	CurHitPoints uint16
	Completed    bool
}
