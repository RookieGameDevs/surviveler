/*
 * Surviveler game package
 * world representation
 */
package surviveler

import (
	"bytes"
	"fmt"
	"image"

	log "github.com/Sirupsen/logrus"
	geo "github.com/aurelien-rainone/gogeo"
)

/*
 * World is the spatial reference on which game entities are located
 */
type World struct {
	Grid                                      // the embedded map
	GridWidth, GridHeight int                 // grid dimensions
	Width, Height         float64             // world dimensions
	GridScale             float64             // the grid scale
	Entities              map[uint32]TileList // map entities to the tiles to which it is attached
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
		Entities:   make(map[uint32]TileList),
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
func (w World) TileFromVec(pt geo.Vec2) *Tile {
	return w.Tile(int(pt[0]), int(pt[1]))
}

/*
 * TileFromWorldVec gets the tile at given point in the grid
 *
 * pt represents *world* coordinates, i.e TileFromWorldVec performs the
 * conversion from world coordinates into grid coordinates.
 */
func (w World) TileFromWorldVec(pt geo.Vec2) *Tile {
	pt = pt.Mul(w.GridScale)
	return w.TileFromVec(pt)
}

/*
 * PointInBounds indicates if specific point lies in the world boundaries
 */
func (w World) PointInBounds(pt geo.Vec2) bool {
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
 * IntersectingTiles returns the list of Tile intersecting with an AABB
 */
func (w World) IntersectingTiles(bb geo.BoundingBox) []*Tile {
	// first thing: we need the tile that contains the center of the aabb
	center := w.TileFromWorldVec(bb.Center())
	tiles := []*Tile{center}
	if center.BoundingBox().Contains(bb) {
		// exit now if the aabb is contained in the center tile
		return tiles
	}

	// get the 4 'direct' neighbours
	left := w.Tile(center.X-1, center.Y)
	right := w.Tile(center.X+1, center.Y)
	up := w.Tile(center.X, center.Y-1)
	down := w.Tile(center.X, center.Y+1)

	// intersection with horizontal and vertical neighbour tiles
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

	// intersection with diagonal neighbour tiles
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
	// retrieve list of tiles intersecting with the entity aabb
	tileList := w.IntersectingTiles(ent.BoundingBox())

	// attach this entity to all those tiles
	w.attachTo(ent, tileList...)

	// add those links to the world (for fast query by entity id)
	w.Entities[ent.Id()] = tileList
}

/*
 * DetachEntity detaches an entity from the underlying world representation
 */
func (w *World) DetachEntity(ent Entity) {
	// retrieve tile list for this entity
	tileList := w.Entities[ent.Id()]
	// detach the entity from each of those tiles
	w.detachFrom(ent, tileList...)

	// clear the tile list for this entity
	w.Entities[ent.Id()] = make(TileList, 0)
}

func (w *World) attachTo(ent Entity, tiles ...*Tile) {
	// attach entity to those tiles
	for _, t := range tiles {
		t.Entities.Add(ent)
	}
}

func (w *World) detachFrom(ent Entity, tiles ...*Tile) {
	// detach entity from those tiles
	for _, t := range tiles {
		t.Entities.Remove(ent)
	}
}

/*
 * UpdateEntity updates the entity position on the underlying world
 * representation.
 *
 * This function should preferably be called only if the entity has moved
 * in order to avoid useless computation of intersections
 */
func (w *World) UpdateEntity(ent Entity) {
	// simply detach and re-attach it
	w.DetachEntity(ent)
	w.AttachEntity(ent)
}

/*
 * AABBSpatialQuery returns the set of entities intersecting with given aabb
 *
 * The query is performed on the underlying grid representation from the world, by
 * first retrieving the tiles that intersect with the provided bounding box.
 * As each tile has an always-updated list of entities that intersect with itself,
 * the result of the spatial query is the set of those entities.
 *
 * Important Note: if the query is performed by passing the bounding box of an entity,
 * the returned set will contain this entity.
 */
func (w *World) AABBSpatialQuery(bb geo.BoundingBox) *EntitySet {
	// set to contain all the entities around, though not necessarily colliding
	allEntities := NewEntitySet()

	// loop on the intersecting tiles
	for _, it := range w.IntersectingTiles(bb) {
		// add all the entities attached to this tile
		allEntities.Union(&it.Entities)
	}

	colliding := NewEntitySet()
	// filter out the non-colliding entities
	allEntities.Each(func(ent Entity) bool {
		if ent.BoundingBox().Intersects(bb) {
			colliding.Add(ent)
		}
		return true
	})

	return colliding
}

/*
 * EntitySpatialQuery returns the set of entities intersecting with another.
 *
 * see AABBSpatialQuery. Given Entity is removed from the set of entity
 * returned.
 */
func (w *World) EntitySpatialQuery(ent Entity) *EntitySet {
	set := w.AABBSpatialQuery(ent.BoundingBox())
	if !set.Contains(ent) {
		panic("EntitySpatialQuery should have find the requesting entity... :-(")
	}
	set.Remove(ent)
	return set
}
