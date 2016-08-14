/*
 * Surviveler game package
 * common helper, utility functions
 */
package surviveler

import (
	"server/entities"
	"server/game"
)

/*
 * getPlayer returns the Player associated to given ID.
 *
 * It returns nil if ID doesn't exist or the entity is not a Player.
 */
func (gs *gamestate) getPlayer(ID uint32) *entities.Player {
	if e, ok := gs.entities[ID]; ok {
		if p, ok := e.(*entities.Player); ok {
			return p
		}
	}
	return nil
}

/*
 * getZombie returns the Zombie associated to given ID.
 *
 * It returns nil if ID doesn't exist or the entity is not a Zombie.
 */
func (gs *gamestate) getZombie(ID uint32) *entities.Zombie {
	if e, ok := gs.entities[ID]; ok {
		if z, ok := e.(*entities.Zombie); ok {
			return z
		}
	}
	return nil
}

/*
 * getZombie returns the Object associated to given ID.
 *
 * It returns nil if ID doesn't exist or the entity is not an Object.
 */
func (gs *gamestate) getObject(ID uint32) game.Object {
	if e, ok := gs.entities[ID]; ok {
		if o, ok := e.(game.Object); ok {
			return o
		}
	}
	return nil
}

/*
 * getBuilding returns the Building associated to given ID.
 *
 * It returns nil if ID doesn't exist or the entity is not a Building.
 */
func (gs *gamestate) getBuilding(ID uint32) game.Building {
	if e, ok := gs.entities[ID]; ok {
		if b, ok := e.(game.Building); ok {
			return b
		}
	}
	return nil
}
