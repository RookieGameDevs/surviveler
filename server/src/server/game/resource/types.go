/*
 * Surviveler resource package
 * resource package data types
 */
package resource

type Pos2D []int

/*
 * IsValid checks the semantic validity.
 *
 * In the case of a Pos2D, it checks that the slice is composed of exactly 2
 * values
 */
func (p Pos2D) IsValid() bool {
	// should be made of 2 coordinates
	return len(p) == 2
}

type Rect2D []Pos2D

/*
 * IsValid checks the semantic validity.
 *
 * In the case of a Rect2D, we check that the slice is composed of exactly 2
 * positions and that they are valid
 */
func (r Rect2D) IsValid() bool {
	// should be made of 2 positions
	if len(r) == 2 {
		return r[0].IsValid() && r[1].IsValid()
	}
	return false
}

type Object struct {
	Ref      string `json:"ref"`      // uri of the object inside the package
	Pos      Pos2D  `json:"pos"`      // position of the object on the map
	Rotation int    `json:"rotation"` // rotation of the object on the map
}
