/*
 * Surviveler world package
 * map representation
 */
package world

import ()

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
