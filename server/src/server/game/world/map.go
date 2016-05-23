/*
 * Surviveler world package
 * map representation
 */
package world

import (
	"fmt"
	"io"
)

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
	KindNotWalkable = iota << 0
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
 * World is the spatial reference on which game entities are located
 */
type World struct {
	Map                        // the embedded map
	Xmin, Xmax, Ymin, Ymax int // world boundaries
}

/*
 * BrandNewWorld creates a brand new world
 */
func BrandNewWorld(x1, y1 int, x2, y2 int) *World {
	w := new(World)
	w.Xmin = x1
	w.Xmax = x2
	w.Ymin = y1
	w.Ymax = y2

	// pre allocate all tiles
	w.Map = make(map[int]map[int]*Tile)
	for x := w.Xmin; x < w.Xmax; x++ {
		w.Map[x] = make(map[int]*Tile)
		for y := w.Ymin; y < w.Ymax; y++ {
			w.SetTile(&Tile{
				Kind: KindNotWalkable,
				M:    w.Map,
			}, x, y)
		}
	}
	return w
}

/*
 * Dump writes a string representation of the world in the provided Writer
 */
func (w World) Dump(w_ io.Writer) {
	for y := w.Ymin; y < w.Ymax; y++ {
		for x := w.Xmin; x < w.Xmax; x++ {
			t := w.Tile(x, y)
			io.WriteString(w_, fmt.Sprintf("%2v", t.Kind))
		}
		io.WriteString(w_, "\n")
	}
}
