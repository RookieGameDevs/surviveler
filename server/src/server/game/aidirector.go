/*
 * Surviveler game package
 * AI director
 */
package game

import (
	"errors"
	log "github.com/Sirupsen/logrus"
	"server/game/entity"
	"server/game/resource"
	"server/math"
	"time"
)

// This number represents the ration between the number of logic ticks for one
// AI director tick
const AIDirectorTickUpdate int = 20

/*
 * AIDirector is the system that manages the ingredients a game session
 *
 * The AIDirector makes the game experience fun and unpredictable by:
 * - procedurally populate the environment with interesting distributions of
 *   zombies. To do so it modulates the number of zombies and their spawn point
 *   over time.
 * - modulates the players emotional intensity (affect each player an emotional
 *   intensity and updates it). Emotional intensity decays towards zero over
 *   time if no zombies are around
 */
type AIDirector struct {
	gs            *GameState
	curTick       int
	wandererPaths PathCache // zombie wanderer preprocessed paths
	keypoints     resource.AIKeypoints
}

func (ai *AIDirector) init(gs *GameState) error {
	log.Info("Initializing AI Director")
	ai.gs = gs
	ai.curTick = 0
	ai.keypoints = gs.md.AIKeypoints
	ai.wandererPaths.init(len(ai.keypoints.Spawn.Enemies), len(ai.keypoints.WanderingDest))

	// preprocess zombie wanderers paths
	// from zombie spawn points to wandering destinations
	for i := range ai.keypoints.Spawn.Enemies {
		org := ai.keypoints.Spawn.Enemies[i]
		for j := range gs.md.AIKeypoints.WanderingDest {
			dst := ai.keypoints.WanderingDest[j]

			// run pathfinding
			if path, _, found := ai.gs.pathfinder.FindPath(org, dst); !found {
				log.WithFields(log.Fields{
					"org": org,
					"dst": dst}).
					Error("Failed to find zombie wanderer path")
				return errors.New("Couldn't precompute a zombie wanderer path")
			} else {
				// cache the preprocessed path
				ai.wandererPaths.cachePath(i, j, &path)
			}
		}
	}
	return nil
}

func (ai *AIDirector) summonZombieWanderer() {

}

/*
 * summonZombieMob creates a group of zombies
 */
func (ai *AIDirector) summonZombieMob(qty int, zu entity.ZombieUpdater, org math.Vec2, dst math.Vec2) {
	// TODO: to be implemented!
	for i := 0; i < qty; i++ {
		//zombie
	}
}

func (ai *AIDirector) Update(cur_time time.Time) {
	// limit the update frequency
	ai.curTick++
	if ai.curTick%AIDirectorTickUpdate != 0 {
		return
	}

	// for now we stupidly summon a wanderer zombie every 2 seconds
	ai.summonZombieWanderer()
}

type PathCache struct {
	paths  []*math.Path // the slice of cached paths
	numOrg int          // number of destination paths (used to retrieve the index)
}

func (c *PathCache) init(numOrg, numDst int) {
	c.paths = make([]*math.Path, numOrg*numDst)
	c.numOrg = numOrg
}

func (c *PathCache) cachePath(orgIdx, dstIdx int, path *math.Path) {
	c.paths[orgIdx+dstIdx*c.numOrg] = path
}

func (c *PathCache) path(orgIdx, dstIdx int) *math.Path {
	return c.paths[orgIdx+dstIdx*c.numOrg]
}
