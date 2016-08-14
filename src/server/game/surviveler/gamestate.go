/*
 * Surviveler game package
 * game state structure
 */

package surviveler

import (
	"server/entities"
	"server/game"
	"server/math"
	"server/messages"
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
	gameData    *gameData // game constants/resources coming from assets
	gameTime    int16
	entities    map[uint32]game.Entity // entities currently in game
	numEntities uint32                 // number of entities currently present in the game
	game        *survivelerGame
	world       *game.World
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
 * pack converts the current game state into a GameState message
 */
func (gs *gamestate) pack() *messages.GameState {
	// fill the GameState message
	gsMsg := new(messages.GameState)
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
		log.WithField("type", t).Error("Can't create building, unsupported type")
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
