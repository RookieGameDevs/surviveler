/*
 * Surviveler game package
 * grid world representation
 */

package game

import (
	"fmt"
	gomath "math"
	"server/math"

	log "github.com/Sirupsen/logrus"
	astar "github.com/beefsack/go-astar"
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

func (t Tile) IsWalkable() bool {
	return t.Kind == KindWalkable
}

/*
 * PathNeighbors returns a slice containing the neighbors
 */
func (t *Tile) PathNeighbors() []astar.Pather {
	w := t.W
	neighbors := make([]astar.Pather, 0, 8)

	// up
	upw, leftw, rightw, downw := false, false, false, false
	if up := w.Tile(t.X, t.Y-1); up != nil {
		if up.Kind == KindWalkable {
			upw = true
			neighbors = append(neighbors, up)
		}
	}
	// left
	if left := w.Tile(t.X-1, t.Y); left != nil {
		if left.Kind == KindWalkable {
			leftw = true
			neighbors = append(neighbors, left)
		}
	}
	// down
	if down := w.Tile(t.X, t.Y+1); down != nil {
		if down.Kind == KindWalkable {
			downw = true
			neighbors = append(neighbors, down)
		}
	}
	// right
	if right := w.Tile(t.X+1, t.Y); right != nil {
		if right.Kind == KindWalkable {
			rightw = true
			neighbors = append(neighbors, right)
		}
	}

	// up left
	if upleft := w.Tile(t.X-1, t.Y-1); upleft != nil {
		if upleft.Kind == KindWalkable && upw && leftw {
			neighbors = append(neighbors, upleft)
		}
	}

	// down left
	if downleft := w.Tile(t.X-1, t.Y+1); downleft != nil {
		if downleft.Kind == KindWalkable && downw && leftw {
			neighbors = append(neighbors, downleft)
		}
	}

	// up right
	if upright := w.Tile(t.X+1, t.Y-1); upright != nil {
		if upright.Kind == KindWalkable && upw && rightw {
			neighbors = append(neighbors, upright)
		}
	}

	// down right
	if downright := w.Tile(t.X+1, t.Y+1); downright != nil {
		if downright.Kind == KindWalkable && downw && rightw {
			neighbors = append(neighbors, downright)
		}
	}
	return neighbors
}

/*
 * costFromKind returns the cost associated with a kind of tile
 */
func costFromKind(kind TileKind) float64 {
	switch kind {
	case KindWalkable:
		return 10.0
	case KindNotWalkable:
		return 1000000.0
	}
	log.WithField("kind", kind).Panic("TileKind not implemented")
	return 0.0
}

/*
 * PathNeighborCost returns the exact movement cost to reach a neighbor tile
 */
func (t *Tile) PathNeighborCost(to astar.Pather) float64 {
	tt := to.(*Tile)
	cf := costFromKind(tt.Kind)

	if t.X == tt.X || t.Y == tt.Y {
		// same axis, return the movement cost
		return cf
	}
	// diagonal
	return gomath.Sqrt2 * cf
}

/*
 * PathEstimatedCost estimates the movement cost required to reach a tile
 */
func (t *Tile) PathEstimatedCost(to astar.Pather) float64 {
	n := to.(*Tile)
	return gomath.Abs(float64(n.X-t.X)) + gomath.Abs(float64(n.Y-t.Y))
}
