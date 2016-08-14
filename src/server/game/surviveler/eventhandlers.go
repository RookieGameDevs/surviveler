package surviveler

import (
	"math/rand"
	"server/game"
	"server/game/entities"
	"server/game/events"
	"server/math"

	log "github.com/Sirupsen/logrus"
)

/*
 * event handler for PlayerJoin events
 */
func (gs *gamestate) onPlayerJoin(event *events.Event) {
	evt := event.Payload.(events.PlayerJoin)
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", evt.Id).Info("Received a PlayerJoin event")

	// pick a random spawn point
	org := gs.gameData.mapData.AIKeypoints.Spawn.
		Players[rand.Intn(len(gs.gameData.mapData.AIKeypoints.Spawn.Players))]

	// load entity data
	entityData := gs.EntityData(game.EntityType(evt.Type))
	if entityData == nil {
		return
	}

	// instantiate player with settings from the resources pkg
	p := entities.NewPlayer(gs.game, org, game.EntityType(evt.Type),
		float64(entityData.Speed), float64(entityData.TotalHP),
		uint16(entityData.BuildingPower), uint16(entityData.CombatPower))
	p.SetId(evt.Id)
	gs.AddEntity(p)
}

/*
 * event handler for PlayerLeave events
 */
func (gs *gamestate) onPlayerLeave(event *events.Event) {
	evt := event.Payload.(events.PlayerLeave)
	// one player less, remove him from the map
	log.WithField("clientId", evt.Id).Info("We have one less player")
	delete(gs.entities, evt.Id)
}

/*
 * event handler for PlayerMove events
 */
func (gs *gamestate) onPlayerMove(event *events.Event) {
	evt := event.Payload.(events.PlayerMove)
	log.WithField("evt", evt).Info("Received PlayerMove event")

	if player := gs.getPlayer(evt.Id); player != nil {
		// set player action
		player.Move()
		// plan movement
		gs.fillMovementRequest(player, math.FromFloat32(evt.Xpos, evt.Ypos))
	}
}

/*
 * event handler for PlayerBuild events
 */
func (gs *gamestate) onPlayerBuild(event *events.Event) {
	evt := event.Payload.(events.PlayerBuild)
	log.WithField("evt", evt).Info("Received PlayerBuild event")

	if player := gs.getPlayer(evt.Id); player != nil {

		// check entity type because only engineers can build
		if player.Type() != game.EngineerEntity {
			gs.game.clients.Kick(evt.Id,
				"illegal action: only engineers can build!")
			return
		}

		// get the tile at building point coordinates
		tile := gs.world.TileFromWorldVec(math.FromFloat32(evt.Xpos, evt.Ypos))

		// tile must be walkable
		if !tile.IsWalkable() {
			log.WithField("tile", tile).
				Error("Tile is not walkable: can't build")
			return
		}

		// check if we can build here
		tile.Entities.Each(func(ent game.Entity) bool {
			if _, ok := ent.(game.Building); ok {
				log.WithField("tile", tile).
					Error("There's already a building on this tile")
				return false
			}
			return true
		})

		// clip building center with tile center
		pos := math.FromInts(tile.X, tile.Y).
			Div(gs.world.GridScale).
			Add(txCenter)

		// create the building, attach it to the tile
		building := gs.createBuilding(game.EntityType(evt.Type), pos)

		// set player action
		player.Build(building)

		// plan movement
		gs.fillMovementRequest(player, pos)
	}
}

/*
 * event handler for PlayerRepair events
 */
func (gs *gamestate) onPlayerRepair(event *events.Event) {
	evt := event.Payload.(events.PlayerRepair)
	log.WithField("evt", evt).Info("Received PlayerRepair event")

	if player := gs.getPlayer(evt.Id); player != nil {

		if building := gs.getBuilding(evt.BuildingId); building != nil {
			// set player action
			player.Repair(building)

			// plan movement
			gs.fillMovementRequest(player, building.Position())
		}
	}
}

/*
 * event handler for PlayerAttack events
 */
func (gs *gamestate) onPlayerAttack(event *events.Event) {
	evt := event.Payload.(events.PlayerAttack)
	log.WithField("evt", evt).Info("Received PlayerAttack event")

	if player := gs.getPlayer(evt.Id); player != nil {

		if enemy := gs.getZombie(evt.EntityId); enemy != nil {
			// set player action
			player.Attack(enemy)
		}
	}
}

/*
 * event handler for PlayerUse events
 */
func (gs *gamestate) onPlayerOperate(event *events.Event) {
	evt := event.Payload.(events.PlayerOperate)
	log.WithField("evt", evt).Info("Received PlayerOperate event")

	if player := gs.getPlayer(evt.Id); player != nil {

		if object := gs.getObject(evt.EntityId); object != nil {
			// get the tile at building point coordinates
			tile := gs.world.TileFromWorldVec(object.Position())

			var draft *game.Tile
			var position *math.Vec2

			// This is awful, isn't it?
			// FIXME: please, at some point...
			for x := tile.X - 1; x <= tile.X+1; x++ {
				if position != nil {
					break
				}
				for y := tile.Y - 1; y <= tile.Y+1; y++ {
					if position != nil {
						break
					}
					if x != tile.X && y != tile.Y {
						draft = gs.world.Tile(x, y)
						if draft.IsWalkable() {
							position = &math.Vec2{
								float64(x) / gs.world.GridScale,
								float64(y) / gs.world.GridScale,
							}
						}
					}
				}
			}

			if position != nil {
				// set player action
				player.Operate(object)

				// plan movement
				gs.fillMovementRequest(player, *position)
			}
		}
	}
}

/*
 * event handler for PlayerDeath events
 */
func (gs *gamestate) onPlayerDeath(event *events.Event) {
	evt := event.Payload.(events.PlayerDeath)
	log.WithField("evt", evt).Info("Received PlayerDeath event")

	// TODO: we should keep track of what is happening and maybe mark the
	// entity as dead and then remove it later.
	if player := gs.getPlayer(evt.Id); player != nil {
		gs.game.clients.Disconnect(evt.Id, "player got killed")
		gs.RemoveEntity(evt.Id)
	}
}

/*
 * event handler for EnemyDeath events
 */
func (gs *gamestate) onZombieDeath(event *events.Event) {
	evt := event.Payload.(events.ZombieDeath)
	log.WithField("evt", evt).Info("Received ZombieDeath event")

	// TODO: we should keep track of what is happening and maybe mark the
	// entity as dead and then remove it later.
	if zombie := gs.getZombie(evt.Id); zombie != nil {
		gs.RemoveEntity(evt.Id)
	}
}

/*
 * event handler for BuildingDestroy events
 */
func (gs *gamestate) onBuildingDestroy(event *events.Event) {
	evt := event.Payload.(events.BuildingDestroy)
	log.WithField("evt", evt).Info("Received BuildingDestroy event")

	// TODO: we should keep track of what is happening and maybe mark the
	// entity as dead and then remove it later.
	if building := gs.getBuilding(evt.Id); building != nil {
		gs.RemoveEntity(evt.Id)
	}
}
