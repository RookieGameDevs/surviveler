/*
 * actions package
 * action types and definitions
 */
package actions

type Type uint16

// gamestate action types
const (
	IdleId Type = 0 + iota
	MoveId
	BuildId
	RepairId
	AttackId
	DrinkCoffeeId
)

/*
 * Idle action payload
 */
type Idle struct{}

/*
 * Build action payload
 */
type Build struct{}

/*
 * Repair action payload
 */
type Repair struct{}

/*
 * Attack action payload
 */
type Attack struct {
	TargetID uint32
}

/*
 * Drink coffee action payload
 */
type DrinkCoffee struct{}

/*
 * Movement action payload
 */
type Move struct {
	Speed float64
}

/*
 * Action gathers an Action with and its type
 */
//go:generate go-gencon -type Action -cont Stack -name Stack
type Action struct {
	Type Type
	Item interface{}
}

/*
 * NewAction creates a new Action.
 */
func New(t Type, i interface{}) *Action {
	return &Action{Type: t, Item: i}
}
