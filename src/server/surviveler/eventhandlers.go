/*
 * Surviveler package
 * event handlers
 */
package surviveler

import (
	"math/rand"
	"server/events"
	"server/math"

	log "github.com/Sirupsen/logrus"
)

/*
 * runPathFinder runs the macro-pathfinder from org to dst.
 *
 * The callback function fn is called if a path is found.
 */
func (gs *GameState) runPathFinder(org, dst d2.Vec2, fn func(path d2.Path)) {
	ctxLog := log.WithFields(log.Fields{"org": org, "dst": dst})
	// run the macro-pathfinder
	path, _, found := gs.game.Pathfinder().FindPath(org, dst)
	if !found {
		ctxLog.Warn("Pathfinder failed to find path")
		return
	}

	// TODO: why > 1? it should be forbidden, pathfinder-side, to return an
	// empty path!
	if len(path) > 1 {
		ctxLog.WithField("path", path).Debug("Pathfinder found a path")
		fn(path)
	}
}

/*
 * event handler for PlayerJoin events
 */
func (gs *GameState) onPlayerJoin(event *events.Event) {
	evt := event.Payload.(events.PlayerJoin)
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", evt.Id).Info("Received a PlayerJoin event")

	// pick a random spawn point
	org := gs.gameData.mapData.AIKeypoints.Spawn.
		Players[rand.Intn(len(gs.gameData.mapData.AIKeypoints.Spawn.Players))]

	// load entity data
	entityData := gs.EntityData(EntityType(evt.Type))
	if entityData == nil {
		return
	}

	// instantiate player with settings from the resources pkg
	p := NewPlayer(gs.game, org, EntityType(evt.Type),
		float32(entityData.Speed), float32(entityData.TotalHP),
		uint16(entityData.BuildingPower), uint16(entityData.CombatPower))
	p.SetId(evt.Id)
	gs.AddEntity(p)
}

/*
 * event handler for PlayerLeave events
 */
func (gs *GameState) onPlayerLeave(event *events.Event) {
	evt := event.Payload.(events.PlayerLeave)
	// one player less, remove him from the map
	log.WithField("clientId", evt.Id).Info("We have one less player")
	delete(gs.entities, evt.Id)
}

/*
 * event handler for PlayerMove events
 */
func (gs *GameState) onPlayerMove(event *events.Event) {
	evt := event.Payload.(events.PlayerMove)
	dst := d2.NewVec(evt.Xpos, evt.Ypos)

	ctxLog := log.WithFields(log.Fields{"evt": evt, "dst": dst})
	ctxLog.Info("Received PlayerMove event")

	if !gs.world.PointInBounds(dst) {
		// do not forward a request with out-of-bounds destination
		ctxLog.Error("Can't plan path to out-of-bounds destination")
		return
	}

	player := gs.getPlayer(evt.Id)
	if player == nil {
		ctxLog.Error("Unknown player id")
		return
	}

	gs.runPathFinder(player.Position(), dst, func(p d2.Path) {
		player.Move(p)
	})
}

/*
 * event handler for PlayerBuild events
 */
func (gs *GameState) onPlayerBuild(event *events.Event) {
	evt := event.Payload.(events.PlayerBuild)
	dst := d2.NewVec(evt.Xpos, evt.Ypos)

	ctxLog := log.WithFields(log.Fields{"evt": evt, "dst": dst})
	ctxLog.Info("Received PlayerBuild event")

	player := gs.getPlayer(evt.Id)
	if player == nil {
		ctxLog.Error("Unknown player id")
		return
	}

	// only engineers can build
	if player.Type() != EngineerEntity {
		gs.game.clients.Kick(evt.Id,
			"illegal action: only engineers can build!")
		return
	}
	// get the tile at building point coordinates
	tile := gs.world.TileFromWorldVec(dst)
	ctxLog.WithField("tile", tile)

	// tile must be walkable
	if !tile.IsWalkable() {
		ctxLog.Error("Tile is not walkable: can't build")
		return
	}

	// check if we can build here
	tile.Entities.Each(func(ent Entity) bool {
		if _, ok := ent.(Building); ok {
			ctxLog.Error("There's already a building on this tile")
			return false
		}
		return true
	})

	// clip building center with tile center
	pos := math.FromInts(tile.X, tile.Y).
		Div(gs.world.GridScale).
		Add(txCenter)

	gs.runPathFinder(player.Position(), pos, func(p d2.Path) {
		// create the building, attach it to the tile
		building := gs.createBuilding(EntityType(evt.Type), pos)
		player.Build(building, p)
	})
}

/*
 * event handler for PlayerRepair events
 */
func (gs *GameState) onPlayerRepair(event *events.Event) {
	evt := event.Payload.(events.PlayerRepair)

	ctxLog := log.WithField("evt", evt)
	ctxLog.Info("Received PlayerRepair event")

	player := gs.getPlayer(evt.Id)
	if player == nil {
		ctxLog.Error("Unknown player id")
		return
	}

	building := gs.getBuilding(evt.BuildingId)
	if building == nil {
		ctxLog.Error("Unknown building id")
		return
	}

	gs.runPathFinder(player.Position(), building.Position(), func(p d2.Path) {
		// set player action
		player.Repair(building, p)
	})
}

/*
 * event handler for PlayerAttack events
 */
func (gs *GameState) onPlayerAttack(event *events.Event) {
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
 * event handler for PlayerOperate events
 */
func (gs *GameState) onPlayerOperate(event *events.Event) {
	evt := event.Payload.(events.PlayerOperate)

	ctxLog := log.WithField("evt", evt)
	ctxLog.Info("Received PlayerOperate event")

	player := gs.getPlayer(evt.Id)
	if player == nil {
		ctxLog.Error("Unknown player id")
		return
	}

	object := gs.getObject(evt.EntityId)
	if object == nil {
		ctxLog.Error("Unknown object id")
		return
	}

	var (
		tile, draft *Tile
		position    *math.Vec2
	)

	// get the tile at object coordinates
	tile = gs.world.TileFromWorldVec(object.Position())

	// This is awful, isn't it?
	// FIXME: please, at some point...
	//
	// Yes, this has to and will be fixed as this:
	// when we'll use steering behaviours with entity visibility for
	// micro-pahfinding, we won't have to do this any more, instead we will
	// define the object position as micro-path destination, and the
	// destination reached when the player will collide with this object (as it
	// is now done to detect that an engineer actually reached his target
	// building
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
						float32(x) / gs.world.GridScale,
						float32(y) / gs.world.GridScale,
					}
				}
			}
		}
	}

	if position != nil {
		gs.runPathFinder(player.Position(), *position, func(p d2.Path) {
			player.Operate(object, p)
		})
	}
}

/*
 * event handler for PlayerDeath events
 */
func (gs *GameState) onPlayerDeath(event *events.Event) {
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
 * event handler for ZombieDeath events
 */
func (gs *GameState) onZombieDeath(event *events.Event) {
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
func (gs *GameState) onBuildingDestroy(event *events.Event) {
	evt := event.Payload.(events.BuildingDestroy)
	log.WithField("evt", evt).Info("Received BuildingDestroy event")

	// TODO: we should keep track of what is happening and maybe mark the
	// entity as dead and then remove it later.
	if building := gs.getBuilding(evt.Id); building != nil {
		gs.RemoveEntity(evt.Id)
	}
}
