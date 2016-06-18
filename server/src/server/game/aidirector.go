/*
 * Surviveler game package
 * AI director
 */
package game

import (
	"math/rand"
	"server/game/entity"
	"server/game/resource"
	"time"

	log "github.com/Sirupsen/logrus"
)

// This number represents the ration between the number of logic ticks for one
// AI director tick
const AIDirectorTickUpdate int = 20

// TEMPORARY: add a Zombie every N seconds
const FrequencyAddZombie time.Duration = 5 * time.Second

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
	gs        *GameState
	curTick   int
	keypoints resource.AIKeypoints

	lastTime time.Time
}

func (ai *AIDirector) init(gs *GameState) error {
	log.Info("Initializing AI Director")
	ai.gs = gs
	ai.curTick = 0
	ai.keypoints = gs.md.AIKeypoints
	ai.lastTime = time.Now()
	return nil
}

func (ai *AIDirector) summonZombie() {

	// pick a random spawn point
	org := ai.keypoints.Spawn.Enemies[rand.Intn(len(ai.keypoints.Spawn.Enemies))]

	log.WithFields(log.Fields{
		"spawn": org,
	}).Info("summoning zombie")

	zId := ai.gs.game.AllocEntityId()
	ai.gs.zombies[zId] = entity.NewZombie(org)
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

	// but for now we stupidly summon a zombie every N seconds
	if time.Since(ai.lastTime) > FrequencyAddZombie {
		ai.summonZombie()
		ai.lastTime = time.Now()
	}
}
