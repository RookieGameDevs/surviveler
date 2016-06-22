/*
 * Surviveler entity package
 * action types and definitions
 */
package game

import "server/math"

type ActionType uint16

const (
	IdleAction ActionType = 0 + iota
	MovingAction
)

/*
 * Idle action
 */
type IdleActionData struct {
}

/*
 * Movement action data.
 */
type MoveActionData struct {
	Speed float64
	Path  []math.Vec2
}
