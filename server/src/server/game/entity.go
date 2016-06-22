/*
 * Entity abstractions.
 */
package game

import (
	"server/math"
	"time"
)

/*
 * Enumeration of possible entity types.
 */
type EntityType uint8

/*
 * Entity type identifiers.
 */
const (
	TankEntity EntityType = iota
	ProgrammerEntity
	EngineerEntity
	ZombieEntity
)

/*
 * Entity is the interface that represents stateful game objects
 */
type Entity interface {
	GetType() EntityType
	GetState() EntityState
	GetPosition() math.Vec2
	SetPath(path math.Path)
	Update(dt time.Duration)
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
