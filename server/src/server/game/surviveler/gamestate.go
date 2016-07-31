/*
 * Surviveler game package
 * game state structure
 */

package surviveler

import (
	"math/rand"
	"server/game"
	"server/game/entities"
	"server/game/events"
	msg "server/game/messages"
	"server/math"
	"sort"
	"time"

	log "github.com/Sirupsen/logrus"
)

// translation from topleft of tile to its center
var txCenter math.Vec2

/*
 * gamestate is the structure that contains all the complete game state
 */
type gamestate struct {
	gameData        *gameData // game constants/resources coming from assets
	gameTime        int16
	entities        map[uint32]game.Entity // entities currently in game
	numEntities     uint32                 // number of entities currently present in the game
	game            *survivelerGame
	world           *game.World
	movementPlanner *game.MovementPlanner
}

func newGameState(g *survivelerGame, gameStart int16) *gamestate {
	gs := new(gamestate)
	gs.game = g
	gs.entities = make(map[uint32]game.Entity)
	gs.gameTime = gameStart
	return gs
}

/*
 * init loads configuration from an assets package and initializes various game
 * state sub-structures
 */
func (gs *gamestate) init(gameData *gameData) error {
	// copy pointers
	gs.gameData = gameData
	gs.world = gameData.world

	for _, objdata := range gs.gameData.mapData.UsableObjects {
		switch game.EntityType(objdata.Type) {
		case game.CoffeeMachineObject:
			obj := entities.NewCoffeeMachine(gs.game, objdata.Pos, game.CoffeeMachineObject)
			gs.AddEntity(obj)
		}
	}

	// precompute constant, translation from corner to center of tile
	txCenter = math.Vec2{1.0, 1.0}.Div(2.0 * gs.world.GridScale)
	return nil
}

/*
 * pack converts the current game state into a GameStateMsg
 */
func (gs *gamestate) pack() *msg.GameStateMsg {
	// fill the GameStateMsg
	gsMsg := new(msg.GameStateMsg)
	gsMsg.Tstamp = time.Now().UnixNano() / int64(time.Millisecond)
	gsMsg.Time = gs.gameTime

	// to ease client reception, we separate mobile entities and buildings
	gsMsg.Entities = make(map[uint32]interface{})
	gsMsg.Buildings = make(map[uint32]interface{})
	gsMsg.Objects = make(map[uint32]interface{})

	for id, ent := range gs.entities {
		switch ent.(type) {
		case game.Object:
			gsMsg.Objects[id] = ent.State()
		case game.Building:
			gsMsg.Buildings[id] = ent.State()
		default:
			gsMsg.Entities[id] = ent.State()
		}
	}
	return gsMsg
}

/*
 * event handler for PlayerJoin events
 */
func (gs *gamestate) onPlayerJoin(event *events.Event) {
	evt := event.Payload.(events.PlayerJoinEvent)
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
	evt := event.Payload.(events.PlayerLeaveEvent)
	// one player less, remove him from the map
	log.WithField("clientId", evt.Id).Info("We have one less player")
	delete(gs.entities, evt.Id)
}

/*
 * event handler for PathReadyEvent events
 */
func (gs *gamestate) onPathReady(event *events.Event) {
	evt := event.Payload.(events.PathReadyEvent)
	log.WithField("evt", evt).Info("Received a path ready event")

	if player := gs.getPlayer(evt.Id); player != nil {
		player.SetPath(evt.Path)
	}
}

/*
 * event handler for PlayerMove events
 */
func (gs *gamestate) onPlayerMove(event *events.Event) {
	evt := event.Payload.(events.PlayerMoveEvent)
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
	evt := event.Payload.(events.PlayerBuildEvent)
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
	evt := event.Payload.(events.PlayerRepairEvent)
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
	evt := event.Payload.(events.PlayerAttackEvent)
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
	evt := event.Payload.(events.PlayerOperateEvent)
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
	evt := event.Payload.(events.PlayerDeathEvent)
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
	evt := event.Payload.(events.ZombieDeathEvent)
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
	evt := event.Payload.(events.BuildingDestroyEvent)
	log.WithField("evt", evt).Info("Received BuildingDestroy event")

	// TODO: we should keep track of what is happening and maybe mark the
	// entity as dead and then remove it later.
	if building := gs.getBuilding(evt.Id); building != nil {
		gs.RemoveEntity(evt.Id)
	}
}

/*
 * fillMovementRequest fills up and sends a movement request
 */
func (gs *gamestate) fillMovementRequest(p *entities.Player, dst math.Vec2) {
	if !gs.world.PointInBounds(dst) {
		// do not forward a request with out-of-bounds destination
		log.WithFields(log.Fields{
			"dst":    dst,
			"player": p.Id()}).
			Error("Can't plan path to out-of-bounds destination")
	}

	// fills up a movement request
	mvtReq := game.MovementRequest{}
	mvtReq.Org = p.Position()
	mvtReq.Dst = dst
	mvtReq.EntityID = p.Id()

	// send the request to the movement planner
	gs.movementPlanner.PlanMovement(&mvtReq)
}

/*
 * allocates a new entity identifier.
 */
func (gs *gamestate) allocEntityId() uint32 {
	gs.numEntities++
	return gs.numEntities
}

func (gs *gamestate) World() *game.World {
	return gs.world
}

func (gs *gamestate) Entity(id uint32) game.Entity {
	if ent, ok := gs.entities[id]; ok == true {
		return ent
	}
	return nil
}

/*
 * AddEntity adds an entity to the game state.
 *
 * It entity Id is InvalidID, an unique id is generated and assigned
 * to the entity
 */
func (gs *gamestate) AddEntity(ent game.Entity) {
	id := ent.Id()
	if id == game.InvalidID {
		id = gs.allocEntityId()
		ent.SetId(id)
	}
	gs.entities[id] = ent

	// add the entity onto the world representation
	gs.world.AttachEntity(ent)
}

/*
 * RemoveEntity removes an entity from the game state
 */
func (gs *gamestate) RemoveEntity(id uint32) {
	gs.world.DetachEntity(gs.entities[id])
	delete(gs.entities, id)
}

func (gs *gamestate) createBuilding(t game.EntityType, pos math.Vec2) game.Building {
	var building game.Building
	switch t {
	case game.BarricadeBuilding:
		data := gs.BuildingData(t)
		building = entities.NewBarricade(gs.game, pos, data.TotHp, data.BuildingPowerRec)
	case game.MgTurretBuilding:
		data := gs.BuildingData(t)
		building = entities.NewMgTurret(gs.game, pos, data.TotHp, data.BuildingPowerRec)
	default:
		log.WithField("type", t).Panic("Can't create building, unsupported type")
	}
	gs.AddEntity(building)
	return building
}

func (gs *gamestate) MapData() *MapData {
	return gs.gameData.mapData
}

func (gs *gamestate) EntityData(et game.EntityType) *EntityData {
	entityData, ok := gs.gameData.entitiesData[et]
	if !ok {
		log.WithField("type", et).Error("No resource for this Entity Type")
	}
	return entityData
}

func (gs *gamestate) BuildingData(bt game.EntityType) *BuildingData {
	buildingData, ok := gs.gameData.buildingsData[bt]
	if !ok {
		log.WithField("type", bt).Error("No resource for this Building Type")
	}
	return buildingData
}

func (gs *gamestate) GameTime() int16 {
	return gs.gameTime
}

type entityDist struct {
	e game.Entity
	d float32
}

type entityDistCollection []entityDist

func (c entityDistCollection) Len() int {
	return len(c)
}

func (c entityDistCollection) Less(i, j int) bool {
	return c[i].d < c[j].d
}

func (c entityDistCollection) Swap(i, j int) {
	c[i], c[j] = c[j], c[i]
}

func (gs *gamestate) NearestEntity(pos math.Vec2,
	f game.EntityFilter) (game.Entity, float32) {
	result := make(entityDistCollection, 0)
	for _, ent := range gs.entities {
		if f(ent) {
			result = append(result, entityDist{
				d: float32(ent.Position().Sub(pos).Len()),
				e: ent,
			})
		}
	}
	if len(result) > 0 {
		sort.Sort(result)
		return result[0].e, result[0].d
	}
	return nil, 0
}
