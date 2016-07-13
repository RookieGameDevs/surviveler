/*
 * Surviveler game package
 * grid world representation
 */

package game

import (
	"fmt"
	"server/math"
)

type (
	TileList []*Tile
	Grid     []Tile // Grid is a 2D grid of tiles, mapped onto an 1D slice
	TileKind int
)

// walkability bit constants
const (
	KindNotWalkable TileKind = 0 // non-walkability
	KindWalkable             = 1 // walkability
)

// actual tile kinds (bit 0 is set with walkability mask)
const (
	KindTurret TileKind = 0x10 | KindNotWalkable
)

/*
 * A Tile is a tile in a grid which implements Pather.
 *
 * It implements the BoundingBoxer interface and the fmt.GoStringer interface
 * for commodity.
 */
type Tile struct {
	Kind     TileKind         // kind of tile, each kind has its own cost
	X, Y     int              // tile position in 'grid' coordinates
	W        *World           // reference to the map this tile is part of
	Entities EntitySet        // Entities intersecting with this Tile
	aabb     math.BoundingBox // pre-computed bounding box, as it won't ever change
}

func NewTile(kind TileKind, w *World, x, y int) Tile {
	return Tile{
		Kind:     kind,
		W:        w,
		X:        x,
		Y:        y,
		Entities: *NewEntitySet(),
		aabb: math.BoundingBox{
			MinX: (float64(x) - 0.5) / w.GridScale,
			MaxX: (float64(x) + 0.5) / w.GridScale,
			MinY: (float64(y) - 0.5) / w.GridScale,
			MaxY: (float64(y) + 0.5) / w.GridScale,
		},
	}
}

func (t Tile) GoString() string {
	return fmt.Sprintf("Tile{X: %d, Y: %d, Kind: %d}", t.X, t.Y, t.Kind)
}

func (t Tile) BoundingBox() math.BoundingBox {
	return t.aabb
}
