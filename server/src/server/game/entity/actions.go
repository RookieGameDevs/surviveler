/*
 * Surviveler entity package
 * action types and definitions
 */
package entity

type ActionType uint16

const (
	IdleAction ActionType = 0 + iota
	// TODO: set the real action type Ids
	MovingAction
)

/*
 * EntityState represents a snapshot of an entity
 */
type EntityState struct {
	Tstamp     int64
	Xpos       float32
	Ypos       float32
	ActionType ActionType
	Action     interface{}
}

/*
 * Movement action data.
 */
type MoveActionData struct {
	Speed float32
	Xpos  float32
	Ypos  float32
}

type IdleActionData struct {
	// empty
}
