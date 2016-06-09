/*
 * Surviveler game package
 * world representation
 */
package game

import (
	"bytes"
	"fmt"
	log "github.com/Sirupsen/logrus"
	"image"
	"server/math"
)

/*
 * World is the spatial reference on which game entities are located
 */
type World struct {
	Grid                          // the embedded map
	GridWidth, GridHeight int     // grid dimensions
	Width, Height         float32 // world dimensions
	GridScale             float32 // the grid scale
}

/*
 * Grid is a two dimensional grid of tiles
 */
type Grid []Tile

/*
 * A Tile is a tile in a grid which implements Pather.
 *
 * It implements the fmt.GoStringer interface for commodity.
 */
type Tile struct {
	Kind TileKind // kind of tile, each kind has its own cost
	X, Y int      // 2D coordinates
	W    *World   // reference to the map this is tile is part of
}

func (t Tile) GoString() string {
	return fmt.Sprintf("Tile{X: %d, Y: %d, Kind: %d}", t.X, t.Y, t.Kind)
}

/*
 * NewWorld creates a brand new world.
 *
 * It loads the map from the provided Surviveler Package and initializes the
 * world representation from it.
 */
func NewWorld(img image.Image, gridScale float32) (*World, error) {
	bounds := img.Bounds()
	w := World{
		GridWidth:  bounds.Max.X,
		GridHeight: bounds.Max.Y,
		Width:      float32(bounds.Max.X) / gridScale,
		Height:     float32(bounds.Max.Y) / gridScale,
		GridScale:  gridScale,
	}
	log.WithField("world", w).Info("Building world")

	// allocate tiles
	var kind TileKind
	w.Grid = make([]Tile, bounds.Max.X*bounds.Max.Y)
	for x := bounds.Min.X; x < bounds.Max.X; x++ {
		for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
			r, _, _, _ := img.At(x, y).RGBA()
			if r == 0 {
				kind = KindNotWalkable
			} else {
				kind = KindWalkable
			}
			w.Grid[x+y*w.GridWidth] = Tile{Kind: kind, W: &w, X: x, Y: y}
		}
	}
	return &w, nil
}

type TileKind int

// walkability bit
const (
	KindNotWalkable TileKind = 0 // non-walkability
	KindWalkable             = 1 // walkability
)

// actual tile kinds (bit 0 is set with walkability mask)
const (
	KindTurret TileKind = 0x10 | KindNotWalkable
)

/*
 * Tile gets the tile at the given coordinates in the grid.
 *
 * (x, y) represent *grid* coordinates, i.e the map scale factor must be taken
 * in consideration to convert from *world* coordinates into *grid* coordinates.
 */
func (w World) Tile(x, y int) *Tile {
	switch {
	case x < 0, x >= w.GridWidth, y < 0, y >= w.GridHeight:
		return nil
	default:
		return &w.Grid[x+y*w.GridWidth]
	}
}

/*
 * TileFromVec gets the tile at given point in the grid
 *
 * pt represents *grid* coordinates, i.e the map scale factor must be taken in
 * consideration to convert from *world* coordinates into *grid* coordinates.
 */
func (w World) TileFromVec(pt math.Vec2) *Tile {
	return w.Tile(int(pt[0]), int(pt[1]))
}

/*
 * TileFromWorldVec gets the tile at given point in the grid
 *
 * pt represents *world* coordinates, i.e TileFromWorldVec performs the
 * conversion from world coordinates into grid coordinates.
 */
func (w World) TileFromWorldVec(pt math.Vec2) *Tile {
	pt = pt.Mul(w.GridScale)
	return w.TileFromVec(pt)
}

/*
 * PointInBounds indicates if specific point lies in the world boundaries
 */
func (w World) PointInBounds(pt math.Vec2) bool {
	return pt[0] >= 0 && pt[0] <= w.Width &&
		pt[1] >= 0 && pt[1] <= w.Height
}

/*
 * Dump logs a string representation of the world grid
 */
func (w World) DumpGrid() {
	var buffer bytes.Buffer
	buffer.WriteString("World grid dump:\n")
	for y := 0; y < w.GridHeight; y++ {
		for x := 0; x < w.GridWidth; x++ {
			t := w.Tile(x, y)
			buffer.WriteString(fmt.Sprintf("%2v", t.Kind))
		}
		buffer.WriteString("\n")
	}
	log.Debug(buffer.String())
}
