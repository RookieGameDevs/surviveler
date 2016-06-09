/*
 * Surviveler game package
 * AI director
 */
package game

import (
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
	gs      *GameState
	curTick int
}

func newAIDirector(gs *GameState) *AIDirector {
	return &AIDirector{
		gs:      gs,
		curTick: 0,
	}
}

func (ai *AIDirector) Update(cur_time time.Time) {
	// limit the update frequency
	ai.curTick++
	if ai.curTick%AIDirectorTickUpdate != 0 {
		return
	}
}
