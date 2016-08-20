/*
 * Surviveler package
 * pathfinder implementation
 */
package surviveler

import (
	log "github.com/Sirupsen/logrus"
	geo "github.com/aurelien-rainone/gogeo"
	astar "github.com/beefsack/go-astar"
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
func (pf Pathfinder) FindPath(org, dst geo.Vec2) (path geo.Path, dist float64, found bool) {
	world := pf.game.State().World()
	// scale org and dst coordinates
	scaledOrg, scaledDst := org.Mul(world.GridScale), dst.Mul(world.GridScale)

	// retrieve origin and destination tiles by rounding the scaled org/dst points down
	porg := world.Tile(int(scaledOrg[0]), int(scaledOrg[1]))
	pdst := world.Tile(int(scaledDst[0]), int(scaledDst[1]))
	switch {
	case porg == nil, pdst == nil:
		log.WithFields(log.Fields{"org": org, "dst": dst}).Error("Couldn't find origin or destination Tile")
		found = false
		return
	}

	// perform A*
	rawPath, _, found := astar.Path(porg, pdst)
	if !found {
		return
	}

	// generate a cleaner path, in one pass:
	// - basic path smoothing (remove consecutive equal segments)
	// - clip path segment ends to cell center
	invScale := 1.0 / world.GridScale
	txCenter := geo.Vec2{0.5, 0.5} // tx vector to the cell center
	path = make(geo.Path, 0, len(rawPath))
	var last geo.Vec2
	for pidx := range rawPath {
		tile := rawPath[pidx].(*Tile)
		pt := geo.FromInts(tile.X, tile.Y)
		if pidx == 0 {
			path = append(path, dst)
		} else if pidx == len(rawPath)-1 {
			path = append(path, org)
		} else {
			// basic path smoothing
			dir := last.Sub(pt)
			if pidx+1 < len(rawPath)-1 {
				// there are at least 1 pt between the current one and the last one
				ntile := rawPath[pidx+1].(*Tile)
				npt := geo.FromInts(ntile.X, ntile.Y)
				nextDir := pt.Sub(npt)
				if dir == nextDir {
					last = pt
					continue
				}
			}
			// re-scale coords when adding point to the path
			path = append(path, pt.Add(txCenter).Mul(invScale))
		}
		last = pt
	}
	return
}
