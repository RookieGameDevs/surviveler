/*
 * Surviveler game package
 * pathfinder implementation
 */
package game

import (
	log "github.com/Sirupsen/logrus"
	"github.com/beefsack/go-astar"
	"server/game/entity"
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
func (pf Pathfinder) FindPlayerPath(player *entity.Player, org, dst math.Vec2) (vpath []math.Vec2, dist float64, found bool) {
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

	// TODO: smooth path
	vpath = make([]math.Vec2, 0, len(path))
	for pidx := range path {
		//
		tile := path[pidx].(*Tile)
		vpath = append(vpath, math.Vec2{float32(tile.X), float32(tile.Y)})
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
		neighbors = append(neighbors, up)
	}
	// left
	if left := w.Tile(t.X-1, t.Y); left != nil {
		neighbors = append(neighbors, left)
	}
	// down
	if down := w.Tile(t.X, t.Y+1); down != nil {
		neighbors = append(neighbors, down)
	}
	// right
	if right := w.Tile(t.X+1, t.Y); right != nil {
		neighbors = append(neighbors, right)
	}

	// up left
	if upleft := w.Tile(t.X-1, t.Y-1); upleft != nil {
		neighbors = append(neighbors, upleft)
	}

	// down left
	if downleft := w.Tile(t.X-1, t.Y+1); downleft != nil {
		neighbors = append(neighbors, downleft)
	}

	// up right
	if upright := w.Tile(t.X+1, t.Y-1); upright != nil {
		neighbors = append(neighbors, upright)
	}

	// down right
	if downright := w.Tile(t.X+1, t.Y+1); downright != nil {
		neighbors = append(neighbors, downright)
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
	n := to.(*Tile)
	return costFromKind(n.Kind)
}

/*
 * PathEstimatedCost estimates the movement cost required to reach a tile
 */
func (t *Tile) PathEstimatedCost(to astar.Pather) float64 {
	n := to.(*Tile)
	md := float64(math.Abs(float32(n.X-t.X)) + math.Abs(float32(n.Y-t.Y)))
	return md
}
