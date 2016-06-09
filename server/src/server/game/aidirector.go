/*
 * Surviveler game package
 * AI director
 */
package game

import (
	"server/game/resource"
	"server/math"
	"time"
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
 *
 * It implements the entity.Updater interface
 */
type AIDirector struct {
	zombiesSpawnPoints []math.Vec2
}

func (ai *AIDirector) init(md *resource.MapData) {
	// copy zombie spawn points
	ai.zombiesSpawnPoints = md.Spawn.Ennemies
}

func (ai *AIDirector) Update(dt time.Duration) {
}
