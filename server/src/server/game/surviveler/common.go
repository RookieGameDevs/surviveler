/*
 * Surviveler game package
 * common helper, utility functions
 */
package surviveler

import (
	"fmt"
	"server/game"
	"server/game/entities"
)

/*
 * isPlayer checks if given entity exists and is a player
 */
func (gs *gamestate) isPlayer(id uint32) error {
	if e, ok := gs.entities[id]; !ok {
		return fmt.Errorf("unknown entity id: %v", id)
	} else if _, ok = e.(*entities.Player); !ok {
		return fmt.Errorf("entity %v is not a player", id)
	}
	return nil
}

/*
 * isZombie checks if given entity exists and is a zombie
 */
func (gs *gamestate) isZombie(id uint32) error {
	if e, ok := gs.entities[id]; !ok {
		return fmt.Errorf("unknown entity id: %v", id)
	} else if _, ok = e.(*entities.Zombie); !ok {
		return fmt.Errorf("entity %v is not a zombie", id)
	}
	return nil
}

/*
 * isBuilding checks if given entity exists and is a building
 */
func (gs *gamestate) isBuilding(id uint32) error {
	if e, ok := gs.entities[id]; !ok {
		return fmt.Errorf("unknown entity id: %v", id)
	} else if _, ok = e.(game.Building); !ok {
		return fmt.Errorf("entity %v is not a building", id)
	}
	return nil
}
