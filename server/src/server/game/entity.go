/*
 * Entity abstractions.
 */
package game

import (
	gomath "math"
	"server/math"
	"time"
)

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
	IsBuilt() bool
	InduceBuildPower(bp uint16)
}

/*
 * EntityState represents a snapshot of an entity
 */
type EntityState struct {
	Type       EntityType
	Xpos       float32
	Ypos       float32
	ActionType ActionType
	Action     interface{}
}
