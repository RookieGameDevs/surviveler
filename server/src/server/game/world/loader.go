/*
 * Surviveler world package
 * map loader
 */
package world

import (
	"fmt"
	"server/game/resource"
)

type MapData struct {
	Walkables []resource.Rect2D `json:"walkables"`
	Objects   []resource.Object `json:"objects"`
}

/*
 * LoadWorldFrom initializes a world representation from a SurvivelerPackage
 */
func LoadWorldFrom(pkg resource.SurvivelerPackage) (w *World, err error) {
	w = new(World)
	var data MapData
	if err = pkg.LoadMap(&data); err != nil {
		return
	}
	// semantic validity checks
	if err = data.IsValid(); err != nil {
		return
	}

	// TODO: read map data and fill the World with Tile's

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
