/*
 * Surviveler game package
 * world representation
 */
package game

import (
	"bytes"
	"fmt"
	log "github.com/Sirupsen/logrus"
	"server/game/resource"
	"server/math"
)

const WorldScale float32 = 2.0

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
type Grid map[int]map[int]*Tile

/*
 * A Tile is a tile in a grid which implements Pather.
 */
type Tile struct {
	Kind TileKind // kind of tile, each kind has its own cost
	X, Y int      // 2D coordinates
	W    *World   // reference to the map this is tile is part of
}

/*
 * NewWorld creates a brand new world.
 *
 * It loads the map from the provided Surviveler Package and initializes the
 * world representation from it.
 */
func NewWorld(pkg resource.SurvivelerPackage) (*World, error) {
	// read the world grid from the package
	if img, err := pkg.LoadWorldGrid(); err != nil {
		return nil, err
	} else {
		bounds := img.Bounds()
		w := World{
			GridWidth:  bounds.Max.X,
			GridHeight: bounds.Max.Y,
			Width:      float32(bounds.Max.X) / WorldScale,
			Height:     float32(bounds.Max.Y) / WorldScale,
			GridScale:  WorldScale,
		}
		log.WithFields(log.Fields{"width": w.Width, "height": w.Height}).
			Info("Building world")

		// allocate tiles
		var kind TileKind
		w.Grid = make(map[int]map[int]*Tile)
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			w.Grid[x] = make(map[int]*Tile)
			for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
				r, _, _, _ := img.At(x, y).RGBA()
				if r == 0 {
					kind = KindNotWalkable
				} else {
					kind = KindWalkable
				}
				w.SetTile(&Tile{Kind: kind, W: &w, X: x, Y: y})
			}
		}
		return &w, nil
	}
}

type TileKind int

const (
	KindNotWalkable TileKind = 0
	KindWalkable             = 1
	KindTurret
)

/*
 * Tile gets the tile at the given coordinates in the grid
 */
func (w World) Tile(x, y int) *Tile {
	switch {
	case x < 0, x >= w.GridWidth, y < 0, y >= w.GridHeight:
		return nil
	default:
		return w.Grid[x][y]
	}
}

/*
 * SetTile sets a tile at the given coordinates in the world
 */
func (w *World) SetTile(t *Tile) {
	if w.Grid[t.X] == nil {
		w.Grid[t.X] = map[int]*Tile{}
	}
	w.Grid[t.X][t.Y] = t
	t.W = w
}

/*
 * PointInBound indicates if specific point lies in the world bounds
 */
func (w World) PointInBound(pt math.Vec2) bool {
	return pt[0] >= 0 && pt[0] <= w.Width &&
		pt[1] >= 0 && pt[1] <= w.Height
}

/*
 * Dump logs a string representation of the world
 */
func (w World) Dump() {
	var buffer bytes.Buffer
	buffer.WriteString("World matrix dump:\n")
	for y := 0; y < w.GridHeight; y++ {
		for x := 0; x < w.GridWidth; x++ {
			t := w.Tile(x, y)
			buffer.WriteString(fmt.Sprintf("%2v", t.Kind))
		}
		buffer.WriteString("\n")
	}
	log.Debug(buffer.String())
}
