/*
 * Surviveler game package
 * world representation
 */
package surviveler

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"server/resource"

	yaml "gopkg.in/yaml.v2"

	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/go-detour/detour"
	"github.com/aurelien-rainone/go-detour/recast"
	"github.com/aurelien-rainone/go-detour/sample"
	"github.com/aurelien-rainone/go-detour/sample/tilemesh"
	"github.com/aurelien-rainone/gogeo/f32/d2"
	"github.com/aurelien-rainone/gogeo/f32/d3"
)

/*
 * World is the spatial reference on which game entities are located
 */
type World struct {
	NavMesh               *detour.NavMesh             // navigation mesh
	tileMesh              *tilemesh.TileMesh          // tile nav mesh container/rebuilder
	Grid                                              // the embedded map
	GridWidth, GridHeight int                         // grid dimensions
	Width, Height         float32                     // world dimensions
	GridScale             float32                     // the grid scale
	Entities              map[uint32]TileList         // map entities to the tiles to which it is attached
	MeshQuery             *detour.NavMeshQuery        // navigation mesh query
	QueryFilter           *detour.StandardQueryFilter // navmesh query filter
}

/*
 * NewWorld creates a brand new world.
 *
 * It loads the map from the provided Package item and initializes the
 * world with it.
 */
func NewWorld(pkg resource.Package, mapData *MapData) (*World, error) {
	var (
		item                       resource.Item
		err                        error
		mapURI, navmeshSettingsURI string
		ok                         bool
		r1, r2                     io.ReadCloser
		buf                        []byte
		settings                   recast.BuildSettings
		navMesh                    *detour.NavMesh
	)

	// package must contain the path to wall+floors mesh
	if mapURI, ok = mapData.Resources["walls+floor_mesh"]; !ok {
		return nil, errors.New("'walls+floor_mesh' field not found in map assets")
	}

	navmeshSettingsURI, ok = mapData.Resources["walls+floor_meshsettings"]
	if !ok {
		return nil, errors.New("'walls+floor_meshsettings' field not found in map assets")
	}

	// load settings from yaml file
	if item, err = pkg.Open(navmeshSettingsURI); err != nil {
		return nil, err
	}
	if r1, err = item.Open(); err != nil {
		return nil, err
	}
	defer r1.Close()
	if buf, err = ioutil.ReadAll(r1); err != nil {
		return nil, err
	}
	if err = yaml.Unmarshal(buf, &settings); err != nil {
		return nil, err
	}

	ctx := recast.NewBuildContext(true)
	tileMesh := tilemesh.New(ctx)

	tileMesh.SetSettings(settings)

	// load geometry
	if item, err = pkg.Open(mapURI); err != nil {
		return nil, err
	}

	if r2, err = item.Open(); err != nil {
		return nil, err
	}
	defer r2.Close()
	if err = tileMesh.LoadGeometry(r2); err != nil {
		ctx.DumpLog("")
		return nil, fmt.Errorf("couldn't load mesh %v, %s", mapURI, err)
	}
	if navMesh, ok = tileMesh.Build(); !ok {
		ctx.DumpLog("")
		return nil, fmt.Errorf("couldn't build navmesh for %v", mapURI)
	}
	log.WithField("duration", ctx.AccumulatedTime(recast.TimerTotal)).Info("Built navmesh")

	st, q := detour.NewNavMeshQuery(navMesh, 2048)
	if detour.StatusFailed(st) {
		return nil, st
	}

	//
	// setup query filter
	//

	filter := detour.NewStandardQueryFilter()

	// set area flags
	filter.SetIncludeFlags(sample.PolyFlagsAll ^ (sample.PolyFlagsDisabled | sample.PolyFlagsDoor))
	filter.SetExcludeFlags(sample.PolyFlagsDoor)
	log.Debugf("navmesh query filter flags 0x%x 0x%x\n", filter.IncludeFlags(), filter.ExcludeFlags())

	// set area costs
	filter.SetAreaCost(int32(sample.PolyAreaGround), 1.0)
	filter.SetAreaCost(int32(sample.PolyAreaDoor), 10.0)

	return &World{
		tileMesh:    tileMesh,
		NavMesh:     navMesh,
		MeshQuery:   q,
		QueryFilter: filter,
	}, nil
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
func (w World) TileFromVec(pt d2.Vec2) *Tile {
	return w.Tile(int(pt[0]), int(pt[1]))
}

/*
 * TileFromWorldVec gets the tile at given point in the grid
 *
 * pt represents *world* coordinates, i.e TileFromWorldVec performs the
 * conversion from world coordinates into grid coordinates.
 */
func (w World) TileFromWorldVec(pt d2.Vec2) *Tile {
	pt = pt.Scale(w.GridScale)
	return w.TileFromVec(pt)
}

/*
 * PointInBounds indicates if specific point lies in a valid polygon of the
 * navmesh.
 */
func (w World) PointInBounds(pt d2.Vec2) bool {
	pt3 := d3.Vec3{pt[0], 0, pt[1]}
	ext := d3.Vec3{0.1, 1, 0.1}
	st, ref, _ := w.MeshQuery.FindNearestPoly(pt3, ext, w.QueryFilter)
	if detour.StatusFailed(st) {
		log.WithError(st).Debug("Point not in bounds")
	}
	if !w.NavMesh.IsValidPolyRef(ref) {
		log.WithField("ref", ref).Debug("Invalid poly ref")
	}
	return detour.StatusSucceed(st) && w.NavMesh.IsValidPolyRef(ref)
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
func (w World) IntersectingTiles(bb d2.Rectangle) []*Tile {
	// first thing: we need the tile that contains the center of the aabb
	center := w.TileFromWorldVec(bb.Center())
	tiles := []*Tile{center}
	if bb.In(center.Rectangle()) {
		// exit now if the aabb is contained in the center tile
		return tiles
	}

	// get the 4 'direct' neighbours
	left := w.Tile(center.X-1, center.Y)
	right := w.Tile(center.X+1, center.Y)
	up := w.Tile(center.X, center.Y-1)
	down := w.Tile(center.X, center.Y+1)

	// intersection with horizontal and vertical neighbour tiles
	if left != nil && left.Rectangle().Overlaps(bb) {
		tiles = append(tiles, left)
	} else {
		left = nil
	}
	if right != nil && right.Rectangle().Overlaps(bb) {
		tiles = append(tiles, right)
	} else {
		right = nil
	}
	if up != nil && up.Rectangle().Overlaps(bb) {
		tiles = append(tiles, up)
	} else {
		up = nil
	}
	if down != nil && down.Rectangle().Overlaps(bb) {
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
	//tileList := w.IntersectingTiles(ent.Rectangle())

	// attach this entity to all those tiles
	//w.attachTo(ent, tileList...)

	// add those links to the world (for fast query by entity id)
	//w.Entities[ent.Id()] = tileList
}

/*
 * DetachEntity detaches an entity from the underlying world representation
 */
func (w *World) DetachEntity(ent Entity) {
	// retrieve tile list for this entity
	//tileList := w.Entities[ent.Id()]
	// detach the entity from each of those tiles
	//w.detachFrom(ent, tileList...)

	// clear the tile list for this entity
	//w.Entities[ent.Id()] = make(TileList, 0)
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
func (w *World) AABBSpatialQuery(bb d2.Rectangle) *EntitySet {
	return NewEntitySet()
}

/*
 * EntitySpatialQuery returns the set of entities intersecting with another.
 *
 * see AABBSpatialQuery. Given Entity is removed from the set of entity
 * returned.
 */
func (w *World) EntitySpatialQuery(ent Entity) *EntitySet {
	set := w.AABBSpatialQuery(ent.Rectangle())
	if !set.Contains(ent) {
		panic("EntitySpatialQuery should have find the requesting entity... :-(")
	}
	set.Remove(ent)
	return set
}
