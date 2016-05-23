/*
 * Surviveler world package
 * map loader
 */
package world

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"server/game/resource"
)

type MapData struct {
	WorldBoundaries resource.Rect2D   `json:"world_boundaries"`
	Walkables       []resource.Rect2D `json:"walkables"`
	Objects         []resource.Object `json:"objects"`
}

/*
 * LoadWorldFrom initializes a world representation from a SurvivelerPackage
 */
func LoadWorldFrom(pkg resource.SurvivelerPackage) (*World, error) {
	var data MapData
	if err := pkg.LoadMap(&data); err != nil {
		return nil, err
	}
	// semantic validity checks
	if err := data.IsValid(); err != nil {
		return nil, err
	}

	w := BrandNewWorld(
		data.WorldBoundaries[0][0],
		data.WorldBoundaries[0][1],
		data.WorldBoundaries[1][0],
		data.WorldBoundaries[1][1])

	for i := range data.Walkables {
		tl_pos := data.Walkables[i][0]
		br_pos := data.Walkables[i][1]
		for x := tl_pos[0]; x < br_pos[0]; x++ {
			for y := tl_pos[1]; y < br_pos[1]; y++ {
				t := Tile{
					Kind: KindWalkable,
					M:    w.Map,
				}
				w.SetTile(&t, x, y)
			}
		}
	}

	logw := log.StandardLogger().Writer()
	defer logw.Close()
	w.Dump(logw)
	return w, nil
}

/*
 * IsValid checks the semantic validity
 */
func (md MapData) IsValid() error {

	// validate various fields
	if !md.WorldBoundaries.IsValid() {
		return fmt.Errorf("Invalid 'world boundaries': %v\n", md.WorldBoundaries)
	}
	for i := range md.Walkables {
		if !md.Walkables[i].IsValid() {
			return fmt.Errorf("Invalid 'walkable': %v\n", md.Walkables[i])
		}
	}

	for i := range md.Objects {
		if !md.Objects[i].Pos.IsValid() {
			return fmt.Errorf("Invalid 'object' 'pos' field: %v\n", md.Objects[i].Pos)
		}
		switch md.Objects[i].Rotation {
		case 0, 90, 180, 270:
			break
		default:
			return fmt.Errorf("Invalid 'objects' 'rotation' field: %v\n", md.Objects[i].Rotation)
		}
	}

	// actual semantic validation

	// TODO:  check objects are not outside of world boundaries
	// TODO:  check not objects are inside walkable areas

	return nil
}
