/*
 * Surviveler resource package
 * loader implementation
 */
package resource

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
)

type MapData struct {
	Matrix  [][]TileKind `json:"matrix"`
	Objects []Object     `json:"objects"`
}

/*
 * LoadWorldFrom initializes a world representation from a SurvivelerPackage
 */
func LoadWorldFrom(pkg SurvivelerPackage) (*World, error) {
	var data MapData
	if err := pkg.LoadMap(&data); err != nil {
		return nil, err
	}
	// semantic validity checks
	if err := data.IsValid(); err != nil {
		return nil, err
	} else {
		log.Info("Validating world")
	}

	w := BrandNewWorld(data.Matrix)

	logw := log.StandardLogger().Writer()
	defer logw.Close()
	w.Dump(logw)
	return w, nil
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
