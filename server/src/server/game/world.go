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
	Width, Height         float64 // world dimensions
	GridScale             float64 // the grid scale
}

/*
 * Grid is a two dimensional grid of tiles
 */
type Grid []Tile

/*
 * A Tile is a tile in a grid which implements Pather.
 *
 * It implements the BoundingBoxer interface and the fmt.GoStringer interface
 * for commodity.
 */
type Tile struct {
	Kind     TileKind          // kind of tile, each kind has its own cost
	X, Y     int               // 2D coordinates
	W        *World            // reference to the map this is tile is part of
	Entities map[uint32]Entity // Entities intersecting with this Tile
	aabb     math.BoundingBox  // pre-computed bounding box, as it won't ever change
}

func NewTile(kind TileKind, w *World, x, y int) Tile {
	return Tile{
		Kind:     kind,
		W:        w,
		X:        x,
		Y:        y,
		Entities: make(map[uint32]Entity),
		aabb: math.BoundingBox{
			MinX: w.GridScale*float64(x) - 0.25,
			MaxX: w.GridScale*float64(x) + 0.25,
			MinY: w.GridScale*float64(y) - 0.25,
			MaxY: w.GridScale*float64(y) + 0.25,
		},
	}
}

func (t Tile) GoString() string {
	return fmt.Sprintf("Tile{X: %d, Y: %d, Kind: %d}", t.X, t.Y, t.Kind)
}

func (t Tile) BoundingBox() math.BoundingBox {
	return t.aabb
}

/*
 * NewWorld creates a brand new world.
 *
 * It loads the map from the provided Surviveler Package and initializes the
 * world representation from it.
 */
func NewWorld(img image.Image, gridScale float64) (*World, error) {
	bounds := img.Bounds()
	w := World{
		GridWidth:  bounds.Max.X,
		GridHeight: bounds.Max.Y,
		Width:      float64(bounds.Max.X) / gridScale,
		Height:     float64(bounds.Max.Y) / gridScale,
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
			w.Grid[x+y*w.GridWidth] = NewTile(kind, &w, x, y)
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

/*
 *
 */
func (w World) IntersectingTiles(center Tile, bb math.BoundingBox) []*Tile {
	tiles := []*Tile{}

	// exit now if the aabb is contained in the center tile
	if center.BoundingBox().Contains(bb) {
		return tiles
	}

	left := w.Tile(center.X-1, 0)
	right := w.Tile(center.X+1, 0)
	up := w.Tile(0, center.Y-1)
	down := w.Tile(0, center.Y+1)

	// intersection with horizontal and vertical neighbours
	if left != nil && left.BoundingBox().Intersects(bb) {
		tiles = append(tiles, left)
	} else {
		left = nil
	}
	if right != nil && right.BoundingBox().Intersects(bb) {
		tiles = append(tiles, right)
	} else {
		right = nil
	}
	if up != nil && up.BoundingBox().Intersects(bb) {
		tiles = append(tiles, up)
	} else {
		up = nil
	}
	if down != nil && down.BoundingBox().Intersects(bb) {
		tiles = append(tiles, down)
	} else {
		down = nil
	}

	// intersection with diagonal neighbours
	if left != nil && up != nil {
		tiles = append(tiles, w.Tile(center.X-1, center.Y-1))
	}
	if left != nil && down != nil {
		tiles = append(tiles, w.Tile(center.X-1, center.Y+1))
	}
	if right != nil && up != nil {
		tiles = append(tiles, w.Tile(center.X+1, center.Y-1))
	}
	if right != nil && down != nil {
		tiles = append(tiles, w.Tile(center.X+1, center.Y+1))
	}
	return tiles
}

/*
 * AttachEntity attaches an entity on the underlying world representation
 */
func (w *World) AttachEntity(ent Entity) {
	// retrieve the tile containing entity center
	tile := w.TileFromWorldVec(ent.Position())
	tile.Entities[ent.Id()] = ent

	// find neighbour tiles that intersect with the entity bounding box
	for _, t := range w.IntersectingTiles(*tile, ent.BoundingBox()) {
		// attach entity to this tile
		t.Entities[ent.Id()] = ent
	}
}

/*
 * DetachEntity detaches an entity from the underlying world representation
 */
func (w *World) DetachEntity(ent Entity) {
	// retrieve the tile containing entity center
	tile := w.TileFromWorldVec(ent.Position())
	delete(tile.Entities, ent.Id())

	// find neighbour tiles that intersect with the entity bounding box
	for _, t := range w.IntersectingTiles(*tile, ent.BoundingBox()) {
		// detach entity from this tile
		delete(t.Entities, ent.Id())
	}
}

/*
 * UpdateEntity updates the entity position on the underlying world
 * representation.
 *
 * This function should preferably be called only if the entity has moved
 * in order to avoid useless computation of intersections
 */
func (w *World) UpdateEntity() {
	// TODO: continue here!!
}
