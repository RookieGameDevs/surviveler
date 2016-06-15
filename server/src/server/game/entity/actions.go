/*
 * Surviveler entity package
 * action types and definitions
 */
package entity

import "server/math"

type ActionType uint16

const (
	IdleAction ActionType = 0 + iota
	MovingAction
)

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

/*
 * Idle action
 */
type IdleActionData struct {
}

/*
 * Movement action data.
 */
type MoveActionData struct {
	Speed float32
	Waypoints []math.Vec2
}
