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

/*
 * A Tile is a tile in a grid which implements Pather.
 */
type Tile struct {
	Kind int   // kind of tile, each kind has its own cost
	X, Y int   // 2D coordinates of the world
	W    World // W is a reference to the World that the tile is a part of.
}

/*
 * World is a two dimensional map of Tiles.
 */
type World map[int]map[int]*Tile

/*
 * A Map is the high-level structure for map reading, processing, etc.
 */
type Map struct {
	data  MapData // raw map data as read from the data package
	world World   // world representation, in tiles
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
