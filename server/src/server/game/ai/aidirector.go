/*
 * Surviveler game package
 * AI director
 */
package ai

import (
	log "github.com/Sirupsen/logrus"
	"math/rand"
	"server/game"
	"server/game/events"
	"time"
)

// This number represents the ration between the number of logic ticks for one
// AI director tick
const (
	AIDirectorTickUpdate int           = 20
	FrequencyAddZombie   time.Duration = 30 * time.Second
	MaxZombieCount       int           = 10
	MobZombieCount       int           = 3
)

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
	game        game.Game
	curTick     int
	nightStart  int16
	nightEnd    int16
	lastTime    time.Time
	zombieCount int
	intensity   int
}

func NewAIDirector(game game.Game, nightStart, nightEnd int16) *AIDirector {
	log.Info("Initializing AI Director")
	ai := new(AIDirector)
	ai.game = game
	ai.curTick = 0
	ai.lastTime = time.Now()
	ai.nightStart = nightStart
	ai.nightEnd = nightEnd
	return ai
}

/*
 * event handler for EnemyDeath events
 */
func (ai *AIDirector) OnZombieDeath(event *events.Event) {
	ai.zombieCount--
	ai.intensity++
}

func (ai *AIDirector) SummonZombie() {
	keypoints := ai.game.State().MapData().AIKeypoints
	// pick a random spawn point
	org := keypoints.Spawn.Enemies[rand.Intn(len(keypoints.Spawn.Enemies))]

	log.WithFields(log.Fields{
		"spawn": org,
	}).Info("summoning zombie")

	ai.game.State().AddZombie(org)
	ai.zombieCount++
}

/*
 * summonZombieMob creates a group of zombies
 */
func (ai *AIDirector) summonZombieMob(qty int) {
	keypoints := ai.game.State().MapData().AIKeypoints
	// pick a random spawn point
	idx := rand.Intn(len(keypoints.Spawn.Enemies))
	for i := 0; i < qty; i++ {
		org := keypoints.Spawn.Enemies[(i+idx)%len(keypoints.Spawn.Enemies)]
		ai.game.State().AddZombie(org)
		ai.zombieCount++
	}
}

func (ai *AIDirector) Update(curTime time.Time) {
	// limit the update frequency
	ai.curTick++
	if ai.curTick%AIDirectorTickUpdate != 0 {
		return
	}

	freq := FrequencyAddZombie
	if time.Since(ai.lastTime) > freq && ai.IsNight() && ai.zombieCount < MaxZombieCount {
		if ai.intensity >= 5 {
			n := MaxZombieCount - ai.zombieCount
			if n > MobZombieCount {
				n = MobZombieCount
			}
			ai.summonZombieMob(n)
			ai.intensity -= 5
		} else {
			ai.SummonZombie()
		}
		ai.lastTime = time.Now()
	}
}

/*
 * check if the given current time is in the night time defined by nightStart
 * and nightEnd
 */
func (ai *AIDirector) IsNight() bool {
	now := ai.game.State().GameTime()
	// Actually checks if currentTime is in daytime and return the opposite
	return !(now > ai.nightEnd && now < ai.nightStart)
}
