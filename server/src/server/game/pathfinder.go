/*
 * Surviveler game package
 * pathfinder implementation
 */
package game

import (
	log "github.com/Sirupsen/logrus"
	"github.com/beefsack/go-astar"
	gomath "math"
	"server/math"
)

type Pathfinder struct {
	World *World
}

/*
 * FindPlayerPath searches for the best path for a player to reach a destination.
 *
 * The search is performed with the A* algorithm, running on a matrix shaped graph
 * representing the world.
 */
func (pf Pathfinder) FindPlayerPath(org, dst math.Vec2) (vpath []math.Vec2, dist float64, found bool) {
	// retrieve origin and destination tiles
	porg := pf.World.Tile(int(org[0]), int(org[1]))
	pdst := pf.World.Tile(int(dst[0]), int(dst[1]))
	switch {
	case porg == nil, pdst == nil:
		log.WithFields(log.Fields{"org": org, "dst": dst}).Error("Couldn't find origin or destination Tile")
		found = false
		return
	}

	// perform A*
	path, dist, found := astar.Path(porg, pdst)
	if !found {
		return
	}

	// TODO: path smoothing

	// replace origin and destination with real positions
	vpath = make([]math.Vec2, 0, len(path))
	for pidx := range path {
		if pidx == 0 {
			// replace destination
			vpath = append(vpath, dst)
		} else if pidx == len(path)-1 {
			vpath = append(vpath, org)
		} else {
			tile := path[pidx].(*Tile)
			vpath = append(vpath, math.Vec2{float32(tile.X), float32(tile.Y)})
		}
	}
	return
}

/*
 * PathNeighbors returns a slice containing the neighbors
 */
func (t *Tile) PathNeighbors() []astar.Pather {
	w := t.W
	neighbors := make([]astar.Pather, 0, 8)

	// up
	if up := w.Tile(t.X, t.Y-1); up != nil {
		if up.Kind == KindWalkable {
			neighbors = append(neighbors, up)
		}
	}
	// left
	if left := w.Tile(t.X-1, t.Y); left != nil {
		if left.Kind == KindWalkable {
			neighbors = append(neighbors, left)
		}
	}
	// down
	if down := w.Tile(t.X, t.Y+1); down != nil {
		if down.Kind == KindWalkable {
			neighbors = append(neighbors, down)
		}
	}
	// right
	if right := w.Tile(t.X+1, t.Y); right != nil {
		if right.Kind == KindWalkable {
			neighbors = append(neighbors, right)
		}
	}

	// up left
	if upleft := w.Tile(t.X-1, t.Y-1); upleft != nil {
		if upleft.Kind == KindWalkable {
			neighbors = append(neighbors, upleft)
		}
	}

	// down left
	if downleft := w.Tile(t.X-1, t.Y+1); downleft != nil {
		if downleft.Kind == KindWalkable {
			neighbors = append(neighbors, downleft)
		}
	}

	// up right
	if upright := w.Tile(t.X+1, t.Y-1); upright != nil {
		if upright.Kind == KindWalkable {
			neighbors = append(neighbors, upright)
		}
	}

	// down right
	if downright := w.Tile(t.X+1, t.Y+1); downright != nil {
		if downright.Kind == KindWalkable {
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
	to_ := to.(*Tile)
	cf := costFromKind(to_.Kind)

	if t.X == to_.X || t.Y == to_.Y {
		// same axis, return the movement cost
		return cf
	} else {
		// diagonal
		return gomath.Sqrt2 * cf
	}
}

/*
 * PathEstimatedCost estimates the movement cost required to reach a tile
 */
func (t *Tile) PathEstimatedCost(to astar.Pather) float64 {
	n := to.(*Tile)
	return float64(math.Abs(float32(n.X-t.X)) + math.Abs(float32(n.Y-t.Y)))
}
