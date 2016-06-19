/*
 * Surviveler game package
 * AI director
 */
package ai

import (
	"math/rand"
	"server/game"
	"server/game/entities"
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
	game     game.Game
	curTick  int
	lastTime time.Time
}

func NewAIDirector(game game.Game) *AIDirector {
	log.Info("Initializing AI Director")
	ai := new(AIDirector)
	ai.game = game
	ai.curTick = 0
	ai.lastTime = time.Now()
	return ai
}

func (ai *AIDirector) summonZombie() {
	keypoints := ai.game.GetState().GetMapData().AIKeypoints
	// pick a random spawn point
	org := keypoints.Spawn.Enemies[rand.Intn(len(keypoints.Spawn.Enemies))]

	log.WithFields(log.Fields{
		"spawn": org,
	}).Info("summoning zombie")

	ai.game.GetState().AddEntity(entities.NewZombie(ai.game, org))
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

func (ai *AIDirector) Update(curTime time.Time) {
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
