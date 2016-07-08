/*
 * Surviveler game package
 * game state structure
 */

package surviveler

import (
	"errors"
	"fmt"
	log "github.com/Sirupsen/logrus"
	"image"
	"math/rand"
	"server/game"
	"server/game/entities"
	"server/game/events"
	msg "server/game/messages"
	"server/game/resource"
	"server/math"
	"sort"
	"time"
)

// TODO: this map is hard-coded for now, but will be read from resources
// in the future
var _entityTypes = map[string]game.EntityType{}

// translation from topleft of tile to its center
var txCenter math.Vec2

/*
 * gamestate is the structure that contains all the complete game state
 */
type gamestate struct {
	gameTime        int16
	entities        map[uint32]game.Entity // entities currently in game
	numEntities     uint32                 // number of entities currently present in the game
	game            *survivelerGame
	world           *game.World
	mapData         *resource.MapData
	buildingData    map[game.EntityType]*resource.BuildingData
	entityData      map[game.EntityType]*resource.EntityData
	movementPlanner *game.MovementPlanner
}

func newGameState(g *survivelerGame, gameStart int16) *gamestate {
	gs := new(gamestate)
	gs.game = g
	gs.entities = make(map[uint32]game.Entity)
	gs.entityData = make(map[game.EntityType]*resource.EntityData)
	gs.buildingData = make(map[game.EntityType]*resource.BuildingData)
	gs.gameTime = gameStart

	// TODO: this map is hard-coded for now, but will be read from resources
	// in the future
	_entityTypes["grunt"] = game.TankEntity
	_entityTypes["engineer"] = game.EngineerEntity
	_entityTypes["zombie"] = game.ZombieEntity
	_entityTypes["mg_turret"] = game.MgTurretBuilding
	return gs
}

/*
 * init loads configuration from an assets package and initializes various game
 * state sub-structures
 */
func (gs *gamestate) init(pkg resource.SurvivelerPackage) error {
	var err error
	// load map data and information
	if gs.mapData, err = pkg.LoadMapData(); err != nil {
		return err
	}
	if gs.mapData.ScaleFactor == 0 {
		err = errors.New("'scale_factor' can't be 0")
	}
	// package must contain the path to world matrix bitmap
	if fname, ok := gs.mapData.Resources["matrix"]; !ok {
		err = errors.New("'matrix' field not found in the map asset")
	} else {
		var worldBmp image.Image
		if worldBmp, err = pkg.LoadBitmap(fname); err == nil {
			if gs.world, err =
				game.NewWorld(worldBmp, gs.mapData.ScaleFactor); err == nil {
				err = gs.validateWorld()
			}
		}
	}
	if err != nil {
		return err
	}

	// load entities URI map
	var (
		em *resource.EntitiesData
		t  game.EntityType
		ok bool
	)
	if em, err = pkg.LoadEntitiesData(); err != nil {
		return err
	}
	for name, uri := range em.Entities {
		var entityData resource.EntityData
		if pkg.LoadJSON(uri, &entityData); err != nil {
			return err
		} else {
			if t, ok = _entityTypes[name]; !ok {
				return fmt.Errorf("Couldn't find type of '%s' entity", name)
			}
			log.WithFields(
				log.Fields{"name": name, "type": t, "data": entityData}).
				Debug("Loaded EntityData")
			gs.entityData[t] = &entityData
		}
	}
	for name, uri := range em.Buildings {
		var buildingData resource.BuildingData
		if pkg.LoadJSON(uri, &buildingData); err != nil {
			return err
		} else {
			if t, ok = _entityTypes[name]; !ok {
				return fmt.Errorf("Couldn't find type of '%s' building", name)
			}
			log.WithFields(log.Fields{"name": name, "type": t, "data": buildingData}).
				Debug("Loaded BuildingData")
			gs.buildingData[t] = &buildingData
		}
	}
	return err
}

/*
 * validateWorld performs some logical and semantic checks on the loaded world
 */
func (gs *gamestate) validateWorld() error {
	spawnPoints := gs.mapData.AIKeypoints.Spawn
	// validate player spawn point
	for i := range spawnPoints.Players {
		pt := gs.world.TileFromWorldVec(spawnPoints.Players[i])
		if pt == nil {
			return fmt.Errorf(
				"Player spawn point is out of bounds (%#v)",
				spawnPoints.Players[i])
		}
		if pt.Kind&game.KindWalkable == 0 {
			return fmt.Errorf(
				"Player spawn point is located on a non-walkable point: (%#v)",
				*pt)
		}
	}
	// validate enemies spawn points
	if len(spawnPoints.Enemies) == 0 {
		return errors.New("At least one enemy spawn point must be defined")
	}
	for i := range spawnPoints.Enemies {
		zt := gs.world.TileFromWorldVec(spawnPoints.Enemies[i])
		if zt == nil {
			return fmt.Errorf(
				"A Zombie spawn point is out of bounds: (%#v)",
				spawnPoints.Enemies[i])
		}
		if zt.Kind&game.KindWalkable == 0 {
			return fmt.Errorf(
				"A Zombie spawn point is located on a non-walkable tile: (%#v)",
				*zt)
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

	for id, ent := range gs.entities {
		switch ent.(type) {
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
	org := gs.mapData.AIKeypoints.Spawn.
		Players[rand.Intn(len(gs.mapData.AIKeypoints.Spawn.Players))]

	// load entity data
	et := game.EntityType(evt.Type)
	if entityData := gs.EntityData(et); entityData == nil {
		return
	} else {
		// instantiate player with settings from the resources pkg
		p := entities.NewPlayer(gs, org, game.EntityType(evt.Type),
			float64(entityData.Speed), uint16(entityData.BuildingPower))
		p.SetId(evt.Id)
		gs.AddEntity(p)
	}
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
func (gs *gamestate) OnPlayerMove(event *events.Event) {
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
		if tile.Building != nil {
			log.WithField("tile", tile).
				Error("There's already a building on this tile")
			return
		}

		// clip building center with tile center
		pos := math.FromInts(tile.X, tile.Y).
			Div(gs.world.GridScale).
			Add(txCenter)

		// create the building, attach it to the tile
		building := gs.createBuilding(game.EntityType(evt.Type), pos)
		tile.Building = building

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
 * fillMovementRequest fills up and sends a movement request
 */
func (gs *gamestate) fillMovementRequest(p *entities.Player, dst math.Vec2) {
	if gs.world.PointInBounds(dst) {
		// fills up a movement request
		mvtReq := game.MovementRequest{}
		mvtReq.Org = p.Position()
		mvtReq.Dst = dst
		mvtReq.EntityId = p.Id()
		// and send if to the movement planner
		gs.movementPlanner.PlanMovement(&mvtReq)
	} else {
		// do not forward a request with out-of-bounds destination
		log.WithFields(log.Fields{
			"dst":    dst,
			"player": p.Id()}).
			Error("Can't plan path to out-of-bounds destination")
	}
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
 * It entity Id is InvalidId, an unique id is generated and assigned
 * to the entity
 */
func (gs *gamestate) AddEntity(ent game.Entity) {
	id := ent.Id()
	if id == game.InvalidId {
		id = gs.allocEntityId()
		ent.SetId(id)
	}
	gs.entities[id] = ent
}

/*
 * RemoveEntity removes an entity from the game state
 */
func (gs *gamestate) RemoveEntity(id uint32) {
	delete(gs.entities, id)
}

func (gs *gamestate) createBuilding(t game.EntityType, pos math.Vec2) game.Building {
	var building game.Building
	switch t {
	case game.MgTurretBuilding:
		data := gs.BuildingData(t)
		building = entities.NewMgTurret(pos, data.TotHp, data.BuildingPowerRec)
	default:
		log.WithField("type", t).Panic("Can't create building, unsupported type")
	}
	gs.AddEntity(building)
	return building
}

func (gs *gamestate) MapData() *resource.MapData {
	return gs.mapData
}

func (gs *gamestate) EntityData(et game.EntityType) *resource.EntityData {
	entityData, ok := gs.entityData[et]
	if !ok {
		log.WithField("type", et).Error("No resource for this Entity Type")
	}
	return entityData
}

func (gs *gamestate) BuildingData(bt game.EntityType) *resource.BuildingData {
	buildingData, ok := gs.buildingData[bt]
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
