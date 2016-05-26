/*
 * Surviveler game package
 * world representation
 */
package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"io"
)

/*
 * World is the spatial reference on which game entities are located
 */
type World struct {
	Map               // the embedded map
	Width, Height int // world dimensions
}

/*
 * NewWorld creates a brand new world.
 *
 * It loads the map from the provided Surviveler Package and initializes the
 * world representation from it.
 */
func NewWorld(pkg SurvivelerPackage) (*World, error) {
	// read and parse the map in the package
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

	w := World{
		Width:  len(data.matrix[0]),
		Height: len(data.matrix),
	}
	log.WithFields(log.Fields{"width": w.Width, "height": w.Height}).
		Info("Building world")

	// allocate tiles
	w.Map = make(map[int]map[int]*Tile)
	for x := 0; x < w.Width; x++ {
		w.Map[x] = make(map[int]*Tile)
		for y := 0; y < w.Height; y++ {
			kind := data.matrix[y][x]
			w.SetTile(&Tile{
				Kind: kind,
				M:    w.Map,
			}, x, y)
		}
	}

	// dump the world matrix
	logw := log.StandardLogger().Writer()
	defer logw.Close()
	w.Dump(logw)
	return &w, nil
}

type TileKind int

/*
 * A Tile is a tile in a grid which implements Pather.
 */
type Tile struct {
	Kind TileKind // kind of tile, each kind has its own cost
	X, Y int      // 2D coordinates
	M    Map      // reference to the map this is tile is part of
}

const (
	KindNotWalkable TileKind = iota
	KindWalkable
	KindTurret
)

/*
 * Map is a two dimensional map of tiles
 */
type Map map[int]map[int]*Tile

/*
 * Tile gets the tile at the given coordinates in the map
 */
func (w Map) Tile(x, y int) *Tile {
	if w[x] == nil {
		return nil
	}
	return w[x][y]
}

/*
 * SetTile sets a tile at the given coordinates in the world
 */
func (m Map) SetTile(t *Tile, x, y int) {
	if m[x] == nil {
		m[x] = map[int]*Tile{}
	}
	m[x][y] = t
	t.X = x
	t.Y = y
	t.M = m
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
