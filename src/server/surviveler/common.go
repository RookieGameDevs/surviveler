/*
 * Surviveler package
 * common helper, utility functions
 */
package surviveler

/*
 * getPlayer returns the Player associated to given ID.
 *
 * It returns nil if ID doesn't exist or the entity is not a Player.
 */
func (gs *GameState) getPlayer(ID uint32) *Player {
	if e, ok := gs.entities[ID]; ok {
		if p, ok := e.(*Player); ok {
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
func (gs *GameState) getZombie(ID uint32) *Zombie {
	if e, ok := gs.entities[ID]; ok {
		if z, ok := e.(*Zombie); ok {
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
func (gs *GameState) getObject(ID uint32) Object {
	if e, ok := gs.entities[ID]; ok {
		if o, ok := e.(Object); ok {
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
func (gs *GameState) getBuilding(ID uint32) Building {
	if e, ok := gs.entities[ID]; ok {
		if b, ok := e.(Building); ok {
			return b
		}
	}
	return nil
}
