/*
 * Surviveler game package
 * pathfinder implementation
 */
package game

import (
	"server/game/entity"
	"server/math"

	log "github.com/Sirupsen/logrus"
	"github.com/beefsack/go-astar"
)

type Pathfinder struct {
	World *World
}

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

func (t *Tile) PathNeighbors() []astar.Pather {
	w := t.W
	//neighbors := make([]astar.Pather, 0, 8)
	neighbors := []astar.Pather{}

	// up
	up := w.Tile(t.X, t.Y-1)
	upw := true
	if up != nil {
		if upw = up.Kind&KindWalkable == KindWalkable; upw {
			neighbors = append(neighbors, up)
		}
	}

	// left
	left := w.Tile(t.X-1, t.Y)
	leftw := true
	if left != nil {
		if leftw = left.Kind&KindWalkable == KindWalkable; leftw {
			neighbors = append(neighbors, left)
		}
	}

	// down
	down := w.Tile(t.X, t.Y+1)
	downw := true
	if down != nil {
		if downw = down.Kind&KindWalkable == KindWalkable; downw {
			neighbors = append(neighbors, down)
		}
	}

	// right
	right := w.Tile(t.X+1, t.Y)
	rightw := true
	if right != nil {
		if rightw = right.Kind&KindWalkable == KindWalkable; rightw {
			neighbors = append(neighbors, right)
		}
	}

	// up left
	if upw && leftw {
		if upleft := w.Tile(t.X-1, t.Y-1); upleft != nil {
			if upleft.Kind&KindWalkable == KindWalkable {
				neighbors = append(neighbors, upleft)
			}
		}
	}

	// down left
	if downw && leftw {
		if downleft := w.Tile(t.X-1, t.Y+1); downleft != nil {
			if downleft.Kind&KindWalkable == KindWalkable {
				neighbors = append(neighbors, downleft)
			}
		}
	}

	// up right
	if upw && rightw {
		if upright := w.Tile(t.X+1, t.Y-1); upright != nil {
			if upright.Kind&KindWalkable == KindWalkable {
				neighbors = append(neighbors, upright)
			}
		}
	}

	// down right
	if downw && rightw {
		if downright := w.Tile(t.X+1, t.Y+1); downright != nil {
			if downright.Kind&KindWalkable == KindWalkable {
				neighbors = append(neighbors, downright)
			}
		}
	}

	if len(neighbors) == 0 {
		log.WithField("tile", t).Panic("Tile has no neighbors...")
	} else {
		log.WithField("tile", t).Debug("Computed tile neighbors:")
		for _, n := range neighbors {
			log.WithField("n", *n.(*Tile)).Debug("neighbor")
		}
	}

	return neighbors
}

func (t *Tile) PathNeighborCost(to astar.Pather) float64 {
	n := to.(*Tile)
	if t.X == n.X || t.Y == n.Y {
		// neighbor has one common coordinate
		return 1.0
	} else {
		// diagonal neighbors
		return 1.42
	}
}

func (t *Tile) PathEstimatedCost(to astar.Pather) float64 {
	n := to.(*Tile)
	md := float64(math.Abs(float32(n.X-t.X)) + math.Abs(float32(n.Y-t.Y)))
	log.WithFields(log.Fields{"md": md, "t": t, "to": to}).Debug("PathEstimatedCost")
	return md
}
