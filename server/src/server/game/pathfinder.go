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

type Path []math.Vec2

/*
 * FindPlayerPath searches for the best path for a player to reach a
 * destination.
 *
 * The search is performed with the A* algorithm, running on a matrix-shaped
 * graph representing the world. The grid is scaled to achieve a better
 * resolution
 */
func (pf Pathfinder) FindPlayerPath(org, dst math.Vec2) (path Path, dist float64, found bool) {
	// scale org and dst coordinates
	scaledOrg, scaledDst := org.Mul(pf.World.GridScale), dst.Mul(pf.World.GridScale)

	// retrieve origin and destination tiles by rounding the scaled org/dst points down
	porg := pf.World.Tile(int(scaledOrg[0]), int(scaledOrg[1]))
	pdst := pf.World.Tile(int(scaledDst[0]), int(scaledDst[1]))
	switch {
	case porg == nil, pdst == nil:
		log.WithFields(log.Fields{"org": org, "dst": dst}).Error("Couldn't find origin or destination Tile")
		found = false
		return
	}

	// perform A*
	rawPath, dist, found := astar.Path(porg, pdst)
	if !found {
		return
	}

	// generate a cleaner path, in one pass:
	// - basic path smoothing (remove consecutive equal segments)
	// - clip destination to cell center
	invScale := 1.0 / pf.World.GridScale
	path = make([]math.Vec2, 0, len(rawPath))
	var last math.Vec2
	for pidx := range rawPath {
		tile := rawPath[pidx].(*Tile)
		pt := math.Vec2{float32(tile.X), float32(tile.Y)}
		if pidx == 0 {
			// clip destination
			path = append(path, math.Vec2{0.5 + float32(tile.X), 0.5 + float32(tile.Y)}.Mul(invScale))
		} else if pidx == len(path)-1 {
			path = append(path, org)
		} else {
			// basic path smoothing
			dir := last.Sub(pt)
			if pidx+1 < len(rawPath)-1 {
				// there are at least 1 pt between the current one and the last one
				ntile := rawPath[pidx+1].(*Tile)
				npt := math.Vec2{float32(ntile.X), float32(ntile.Y)}
				nextDir := pt.Sub(npt)
				if dir == nextDir {
					last = pt
					continue
				}
			}
			// re-scale coords when adding point to the path
			path = append(path, pt.Mul(invScale))
		}
		last = pt
	}
	log.WithFields(log.Fields{"raw path length": len(rawPath), "smoothed path length": len(path)}).Debug("Path smoothing result")
	return
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
