/*
 * Surviveler game package
 * pathfinder implementation
 */
package game

import (
	"github.com/beefsack/go-astar"
	"server/game/entity"
	"server/math"
)

type Pathfinder struct {
	World *World
}

func (pf Pathfinder) FindPlayerPath(player *entity.Player, org, dst math.Vec2) (vpath []math.Vec2, dist float64, found bool) {
	t1 := pf.World.Tile(int(org[0]), int(org[1]))
	t2 := pf.World.Tile(int(dst[0]), int(dst[1]))
	path, dist, found := astar.Path(t1, t2)
	if !found {
		return
	}

	// TODO: smooth path
	vpath = make([]math.Vec2, len(path))
	for pidx := range path {
		//
		tile := path[pidx].(*Tile)
		vpath = append(vpath, math.Vec2{float32(tile.X), float32(tile.Y)})
	}
	return
}

func (t *Tile) PathNeighbors() []astar.Pather {
	return []astar.Pather{
		t.Up(),
		t.Right(),
		t.Down(),
		t.Left(),
	}
}

func (t *Tile) PathNeighborCost(to astar.Pather) float64 {
	return to.MovementCost
}

func (t *Tile) PathEstimatedCost(to astar.Pather) float64 {
	return t.ManhattanDistance(to)
}
