/*
 * Surviveler resource package
 * loader implementation
 */
package resource

import (
	"fmt"
)

type MapData struct {
	Matrix  [][]int  `json:"matrix"`
	Objects []Object `json:"objects"`
}

/*
 * IsValid checks the semantic validity
 */
func (md MapData) IsValid() error {

	// minimal size for a functionning map is 3x3:
	// 1 walkable cell surrounded by walls
	height := len(md.Matrix)
	if height < 3 {
		return fmt.Errorf("Minimal matrix height is 3")
	}
	width := len(md.Matrix[0])
	if width < 3 {
		return fmt.Errorf("Minimal matrix width is 3")
	}

	// check all rows have the same width
	for row := 0; row < height; row++ {
		if len(md.Matrix[row]) != width {
			return fmt.Errorf("width the of rows 0 and %v differs (%v != %v)",
				row, width, len(md.Matrix[row]))
		}
	}

	for i := range md.Objects {
		if !md.Objects[i].Pos.IsValid() {
			return fmt.Errorf("Invalid 'object' 'pos' field: %v\n",
				md.Objects[i].Pos)
		}
		switch md.Objects[i].Rotation {
		case 0, 90, 180, 270:
			break
		default:
			return fmt.Errorf("Invalid 'objects' 'rotation' field: %v\n",
				md.Objects[i].Rotation)
		}
	}
	return nil
}
