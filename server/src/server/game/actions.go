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
	RepairingAction
)

/*
 * Idle action payload
 */
type IdleActionData struct{}

/*
 * Building action payload
 */
type BuildActionData struct{}

/*
 * Repairing action payload
 */
type RepairActionData struct{}

/*
 * Movement action payload
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
