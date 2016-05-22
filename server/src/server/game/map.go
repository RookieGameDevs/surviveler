/*
 * Surviveler game package
 * map representation
 */
package game

import (
	"fmt"
	"server/game/resource"
)

type MapData struct {
	Walkables []resource.Rect2D `json:"walkables"`
	Objects   []resource.Object `json:"objects"`
}

type Map struct {
	data MapData
}

/*
 * LoadFrom initializes a map from a SurvivelerPackage
 */
func (m *Map) LoadFrom(pkg resource.SurvivelerPackage) (err error) {
	if err = pkg.LoadMap(&m.data); err != nil {
		return
	}
	// semantic validity checks
	if err = m.data.IsValid(); err != nil {
		return
	}
	return
}

/*
 * IsValid checks the semantic validity
 */
func (md MapData) IsValid() error {
	for i := range md.Walkables {
		if !md.Walkables[i].IsValid() {
			return fmt.Errorf("Invalid 'walkables' field: %v\n", md.Walkables[i])
		}
	}
	for i := range md.Objects {
		if !md.Objects[i].Pos.IsValid() {
			return fmt.Errorf("Invalid 'objects.pos' field: %v\n", md.Objects[i].Pos)
		}
		switch md.Objects[i].Rotation {
		case 0, 90, 180, 270:
			break
		default:
			return fmt.Errorf("Invalid 'objects.rotation' field: %v\n", md.Objects[i].Rotation)
		}
	}
	return nil
}
