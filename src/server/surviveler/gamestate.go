/*
 * Surviveler package
 * game state structure
 */

package surviveler

import (
	"server/math"
	"server/messages"
	"sort"
	"time"

	log "github.com/Sirupsen/logrus"
)

// translation from topleft of tile to its center
var txCenter math.Vec2

type EntityFilter func(e Entity) bool

/*
 * gamestate is the structure that contains all the complete game state
 */
type GameState struct {
	gameData    *gameData         // game constants/resources coming from assets
	gameTime    int16             // current time in-game
	entities    map[uint32]Entity // entities currently in game
	numEntities uint32            // number of entities currently present in the game
	game        *Game
	world       *World
}

func newGameState(g *Game, gameStart int16) *GameState {
	gs := new(GameState)
	gs.game = g
	gs.entities = make(map[uint32]Entity)
	gs.gameTime = gameStart
	return gs
}

/*
 * init loads configuration from an assets package and initializes various game
 * state sub-structures
 */
func (gs *GameState) init(gameData *gameData) error {
	// copy pointers
	gs.gameData = gameData
	gs.world = gameData.world

	for _, objdata := range gs.gameData.mapData.UsableObjects {
		switch EntityType(objdata.Type) {
		case CoffeeMachineObject:
			obj := NewCoffeeMachine(gs.game, objdata.Pos, CoffeeMachineObject)
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
func (gs *GameState) pack() *messages.GameState {
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
		case Object:
			gsMsg.Objects[id] = ent.State()
		case Building:
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
func (gs *GameState) allocEntityId() uint32 {
	gs.numEntities++
	return gs.numEntities
}

func (gs *GameState) World() *World {
	return gs.world
}

func (gs *GameState) Entity(id uint32) Entity {
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
func (gs *GameState) AddEntity(ent Entity) {
	id := ent.Id()
	if id == InvalidID {
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
func (gs *GameState) RemoveEntity(id uint32) {
	gs.world.DetachEntity(gs.entities[id])
	delete(gs.entities, id)
}

func (gs *GameState) createBuilding(t EntityType, pos math.Vec2) Building {
	var building Building
	switch t {
	case BarricadeBuilding:
		data := gs.BuildingData(t)
		building = NewBarricade(gs.game, pos, data.TotHp, data.BuildingPowerRec)
	case MgTurretBuilding:
		data := gs.BuildingData(t)
		building = NewMgTurret(gs.game, pos, data.TotHp, data.BuildingPowerRec)
	default:
		log.WithField("type", t).Error("Can't create building, unsupported type")
	}
	gs.AddEntity(building)
	return building
}

func (gs *GameState) MapData() *MapData {
	return gs.gameData.mapData
}

func (gs *GameState) EntityData(et EntityType) *EntityData {
	entityData, ok := gs.gameData.entitiesData[et]
	if !ok {
		log.WithField("type", et).Error("No resource for this Entity Type")
	}
	return entityData
}

func (gs *GameState) BuildingData(bt EntityType) *BuildingData {
	buildingData, ok := gs.gameData.buildingsData[bt]
	if !ok {
		log.WithField("type", bt).Error("No resource for this Building Type")
	}
	return buildingData
}

func (gs *GameState) GameTime() int16 {
	return gs.gameTime
}

type entityDist struct {
	e Entity
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

func (gs *GameState) NearestEntity(pos math.Vec2,
	f EntityFilter) (Entity, float32) {
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
