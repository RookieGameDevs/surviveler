/*
 * Surviveler entity package
 * action types and definitions
 */
package game

import "server/math"

type ActionType uint16

// gamestate action types
const (
	IdleAction ActionType = 0 + iota
	MovingAction
	BuildingAction
)

/*
 * Idle action
 */
type IdleActionData struct {
}

/*
 * Building action
 */
type BuildActionData struct {
}

/*
 * Movement action data.
 */
type MoveActionData struct {
	Speed float64
	Path  []math.Vec2
}

/*
 * Action is a structure packing an concrete Action alongside its type.
 *
 * Its sole purpose is to be used inside containers.
 */
//go:generate go-gencon -type Action -cont Stack
type Action struct {
	Type ActionType
	Item interface{}
}
