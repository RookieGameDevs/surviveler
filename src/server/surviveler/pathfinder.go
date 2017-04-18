/*
 * Surviveler package
 * pathfinder implementation
 */
package surviveler

import (
	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/go-detour/detour"
	"github.com/aurelien-rainone/gogeo/f32/d2"
	"github.com/aurelien-rainone/gogeo/f32/d3"
)

type Pathfinder struct {
	game *Game
}

func NewPathfinder(game *Game) *Pathfinder {
	return &Pathfinder{
		game: game,
	}
}

/*
 * FindPath searches for the best path to reach a destination in the whole grid.
 *
 * The search is performed with the A* algorithm, running on a matrix-shaped
 * graph representing the world. The grid is scaled to achieve a better
 * resolution.
 */
func (pf Pathfinder) FindPath(org, dst d2.Vec2) (path Path, dist float32, found bool) {
	world := pf.game.State().World()
	path = nil

	var (
		orgRef, dstRef detour.PolyRef // references of org/dst polygon refs
		extents        d3.Vec3        // search distance for polygon search (3 axis)
		st             detour.Status  // detour API status code
		org3d, dst3d   d3.Vec3        // actual org and dst positions in 3D
		closest        d3.Vec3        // used for polygon checking
		posOverPoly    bool           // indicate if a specified point is in or out a poly
	)

	org3d = d3.NewVec3XYZ(org[0], 0, org[1])
	dst3d = d3.NewVec3XYZ(dst[0], 0, dst[1])
	closest = d3.NewVec3()

	// define the extents vector for the nearest polygon query
	extents = d3.NewVec3XYZ(0, 2, 0)

	// check origin polygon
	st, orgRef, _ = world.MeshQuery.FindNearestPoly(org3d, extents, world.QueryFilter)
	if detour.StatusFailed(st) {
		log.WithError(st).Debug("FindNearestPoly failed with %v\n", st)
		return
	} else if orgRef == 0 {
		log.WithField("org", org).Debug("org doesn't intersect any polygons")
		return
	}

	// check origin point lies in a polygon of the navmesh (it should be!)
	st = world.MeshQuery.ClosestPointOnPoly(orgRef, org3d, closest, &posOverPoly)
	if detour.StatusFailed(st) {
		log.WithError(st).Errorf("ClosestPointOnPoly failed with %v\n", st)
	}
	if !posOverPoly {
		log.WithFields(log.Fields{
			"org3d": org3d,
		}).Errorf("FindPath destination doesn't lie in a polygon")
	}

	if !world.NavMesh.IsValidPolyRef(orgRef) {
		log.WithField("orgRef", org).Debug("orgRef is not a valid polyRef")
		return
	}

	// check destination polygon
	st, dstRef, _ = world.MeshQuery.FindNearestPoly(dst3d, extents, world.QueryFilter)
	if detour.StatusFailed(st) {
		log.WithError(st).Debug("FindNearestPoly failed with %v\n", st)
		return
	} else if dstRef == 0 {
		log.WithField("dst", org).Debug("dst doesn't intersect any polygons")
		return
	}

	// check destination point lies in a polygon of the navmesh (it should be!)
	st = world.MeshQuery.ClosestPointOnPoly(dstRef, dst3d, closest, &posOverPoly)
	if detour.StatusFailed(st) {
		log.WithError(st).Errorf("ClosestPointOnPoly failed with %v\n", st)
	}
	if !posOverPoly {
		log.WithFields(log.Fields{
			"org3d": org3d,
		}).Errorf("FindPath destination doesn't lie in a polygon")
	}

	if !world.NavMesh.IsValidPolyRef(dstRef) {
		log.WithField("dstRef", org).Debug("dstRef is not a valid polyRef")
		return
	}

	// Find a path from origin polygon to destination polygon
	var (
		path3d    []detour.PolyRef
		pathCount int
	)
	path3d = make([]detour.PolyRef, 100)
	pathCount, st = world.MeshQuery.FindPath(orgRef, dstRef, org3d, dst3d, world.QueryFilter, path3d)
	if detour.StatusFailed(st) {
		log.WithError(st).Info("query.FindPath failed")
	}

	log.WithField("path3d", path3d[:pathCount]).Debug("3d path found")

	// Find a straight path
	var (
		straightPath      []d3.Vec3
		straightPathFlags []uint8
		straightPathRefs  []detour.PolyRef
		straightPathCount int
		maxStraightPath   int32
	)
	// slices that receive the straight path
	maxStraightPath = 100
	straightPath = make([]d3.Vec3, maxStraightPath)
	for i := range straightPath {
		straightPath[i] = d3.NewVec3()
	}
	straightPathFlags = make([]uint8, maxStraightPath)
	straightPathRefs = make([]detour.PolyRef, maxStraightPath)
	straightPathCount, st = world.MeshQuery.FindStraightPath(org3d, dst3d, path3d[:pathCount], straightPath, straightPathFlags, straightPathRefs, 0)
	if detour.StatusFailed(st) {
		log.WithError(st).Error("query.FindStraightPath failed")
		return
	}

	if (straightPathFlags[0] & detour.StraightPathStart) == 0 {
		log.Error("straightPath start is not flagged StraightPathStart")
		return
	}

	if (straightPathFlags[straightPathCount-1] & detour.StraightPathEnd) == 0 {
		log.Error("straightPath end is not flagged StraightPathEnd")
	}

	// path found
	path = make(Path, straightPathCount)
	for i := 0; i < straightPathCount; i++ {
		waypoint := d2.NewVec2XY(straightPath[i][0], straightPath[i][2])
		path[i] = waypoint
	}
	log.WithField("path", path).Info("Path found")
	return path, 0, true
}
