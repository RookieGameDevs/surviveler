/*
 * Surviveler game package
 * world representation
 */
package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"io"
	"server/game/resource"
)

/*
 * World is the spatial reference on which game entities are located
 */
type World struct {
	Grid              // the embedded map
	Width, Height int // world dimensions
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
	// read and parse the map in the package
	var data resource.MapData
	if err := pkg.LoadMap(&data); err != nil {
		return nil, err
	}
	// semantic validity checks
	if err := data.IsValid(); err != nil {
		return nil, err
	} else {
		log.Info("Validating world")
	}

	w := World{
		Width:  len(data.Matrix[0]),
		Height: len(data.Matrix),
	}
	log.WithFields(log.Fields{"width": w.Width, "height": w.Height}).
		Info("Building world")

	// allocate tiles
	w.Grid = make(map[int]map[int]*Tile)
	for x := 0; x < w.Width; x++ {
		w.Grid[x] = make(map[int]*Tile)
		for y := 0; y < w.Height; y++ {
			kind := data.Matrix[y][x]
			tile := &Tile{
				Kind: TileKind(kind),
				W:    &w,
				X:    x,
				Y:    y,
			}
			w.SetTile(tile)
		}
	}

	// dump the world matrix
	logw := log.StandardLogger().Writer()
	defer logw.Close()
	w.Dump(logw)
	return &w, nil
}

type TileKind int

const (
	KindNotWalkable TileKind = iota
	KindWalkable
	KindTurret
)

/*
 * Tile gets the tile at the given coordinates in the grid
 */
func (w World) Tile(x, y int) *Tile {
	switch {
	case x < 0, x >= w.Width, y < 0, y >= w.Height:
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
 * Dump writes a string representation of the world in the provided Writer
 */
func (w World) Dump(w_ io.Writer) {
	for y := 0; y < w.Height; y++ {
		for x := 0; x < w.Width; x++ {
			t := w.Tile(x, y)
			io.WriteString(w_, fmt.Sprintf("%2v", t.Kind))
		}
		io.WriteString(w_, "\n")
	}
}
