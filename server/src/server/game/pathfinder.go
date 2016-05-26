/*
 * Surviveler game package
 * pathfinder implementation
 */
package game

import (
	log "github.com/Sirupsen/logrus"
	"github.com/beefsack/go-astar"
	"server/math"
)

type Pathfinder struct {
	World *World
}

func (pf Pathfinder) FindPlayerPath(org, dst math.Vec2) (path []math.Vec2, dist float32, found bool) {

	path, distance, found := astar.Path(t1, t2)
	if !found {
		log.WithFields("Could not find path")
	}
}
