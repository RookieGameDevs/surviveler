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

/*
 * getPlayer returns the Player associated to given id.
 *
 * It returns nil in case of error
 */
func (gs *gamestate) getPlayer(id uint32) (p *entities.Player) {
	if e, ok := gs.entities[id]; ok {
		p, ok = e.(*entities.Player)
	}
	return
}

/*
 * getZombie returns the Zombie associated to given id.
 *
 * It returns nil in case of error
 */
func (gs *gamestate) getZombie(id uint32) (z *entities.Zombie) {
	if e, ok := gs.entities[id]; ok {
		z, ok = e.(*entities.Zombie)
	}
	return
}

/*
 * getObject returns the Object associated to given id.
 *
 * It returns nil in case of error
 */
func (gs *gamestate) getObject(id uint32) (z game.Object) {
	if e, ok := gs.entities[id]; ok {
		z, ok = e.(game.Object)
	}
	return
}

/*
 * getBuilding returns the Building associated to given id.
 *
 * It returns nil in case of error
 */
func (gs *gamestate) getBuilding(id uint32) (b game.Building) {
	if e, ok := gs.entities[id]; ok {
		b, ok = e.(game.Building)
	}
	return
}
