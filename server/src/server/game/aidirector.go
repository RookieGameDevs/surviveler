/*
 * Surviveler game package
 * AI director
 */
package game

import (
	"errors"
	log "github.com/Sirupsen/logrus"
	"math/rand"
	"server/game/entity"
	"server/game/resource"
	"server/math"
	"time"
)

// This number represents the ration between the number of logic ticks for one
// AI director tick
const AIDirectorTickUpdate int = 20

// TEMPORARY: add a ZombieWanderer every N seconds
const FrequencyAddZombieWanderer time.Duration = 5 * time.Second

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

	lastWandererTime time.Time
}

func (ai *AIDirector) init(gs *GameState) error {
	log.Info("Initializing AI Director")
	ai.gs = gs
	ai.curTick = 0
	ai.keypoints = gs.md.AIKeypoints
	ai.wandererPaths.init(len(ai.keypoints.Spawn.Enemies), len(ai.keypoints.WanderingDest))
	ai.lastWandererTime = time.Now()

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

	// pick a random spawn point
	spawnIdx := rand.Intn(len(ai.keypoints.Spawn.Enemies))
	org := ai.keypoints.Spawn.Enemies[rand.Intn(len(ai.keypoints.Spawn.Enemies))]

	// pick a random wandering destination
	dstIdx := rand.Intn(len(ai.keypoints.WanderingDest))
	dst := ai.keypoints.WanderingDest[dstIdx]

	// retrieve cached path
	path := ai.wandererPaths.path(spawnIdx, dstIdx)

	log.WithFields(log.Fields{
		"spawn": org,
		"dst":   dst,
		"path":  path}).
		Info("summoning wanderer zombie")

	zId := uint32(len(ai.gs.zombies))
	ai.gs.zombies[zId] = entity.NewZombieWanderer(org, *path, 1)
}

/*
 * summonZombieMob creates a group of zombies
 */
func (ai *AIDirector) summonZombieMob(qty int) {
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

	// TODO: improve with emotional intensity!

	// but for now we stupidly summon a wanderer zombie every N seconds
	if time.Since(ai.lastWandererTime) > FrequencyAddZombieWanderer {
		ai.summonZombieWanderer()
		ai.lastWandererTime = time.Now()
	}
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
