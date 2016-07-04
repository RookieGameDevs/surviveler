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

/*
 * gamestate is the structure that contains all the complete game state
 */
type gamestate struct {
	gameTime        int16
	entities        map[uint32]game.Entity // entities currently in game
	numEntities     uint32                 // number of entities currently present in the game
	game            *survivelerGame
	world           *game.World
	md              *resource.MapData
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
func (gs *gamestate) init(pkg resource.SurvivelerPackage) error {
	var err error
	if gs.md, err = pkg.LoadMapData(); err != nil {
		return err
	}
	if gs.md.ScaleFactor == 0 {
		err = errors.New("'scale_factor' can't be 0")
	} else {
		// package must contain the path to world matrix bitmap
		if fname, ok := gs.md.Resources["matrix"]; !ok {
			err = errors.New("'matrix' field not found in the map asset")
		} else {
			var worldBmp image.Image
			if worldBmp, err = pkg.LoadBitmap(fname); err == nil {
				if gs.world, err = game.NewWorld(worldBmp, gs.md.ScaleFactor); err == nil {
					err = gs.validateWorld()
				}
			}
		}
	}
	return err
}

/*
 * validateWorld performs some logical and semantic checks on the loaded world
 */
func (gs *gamestate) validateWorld() error {
	spawnPoints := gs.md.AIKeypoints.Spawn
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
	gsMsg.Entities = make(map[uint32]interface{})
	for id, ent := range gs.entities {
		gsMsg.Entities[id] = ent.State()
	}
	gsMsg.Buildings = make(map[uint32]interface{})
	// TODO: add the real buildings here
	return gsMsg
}

/*
 * event handler for PlayerJoin events
 */
func (gs *gamestate) onPlayerJoin(event *events.Event) {
	evt := event.Payload.(events.PlayerJoinEvent)
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", evt.Id).Info("We have one more player")
	// pick a random spawn point
	org := gs.md.AIKeypoints.Spawn.Players[rand.Intn(len(gs.md.AIKeypoints.Spawn.Players))]
	// TODO: speed from resource
	gs.AddEntity(entities.NewPlayer(
		gs.game, org, 3, game.EntityType(evt.Type)))
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

	// check that the entity exists
	if player, ok := gs.entities[evt.Id]; ok {
		mobileEntity := player.(game.MobileEntity)
		mobileEntity.SetPath(evt.Path)
	}
}

/*
 * event handler for PlayerMove events
 */
func (gs *gamestate) OnPlayerMove(event *events.Event) {
	evt := event.Payload.(events.PlayerMoveEvent)
	log.WithField("evt", evt).Info("Received PlayerMove event")

	// check that the entity exists
	if ent, ok := gs.entities[evt.Id]; ok {
		p := ent.(*entities.Player)
		// set player action
		p.Move()
		// plan movement
		gs.fillMovementRequest(p, math.FromFloat32(evt.Xpos, evt.Ypos))
	}
}

/*
 * event handler for PlayerBuild events
 */
func (gs *gamestate) onPlayerBuild(event *events.Event) {
	evt := event.Payload.(events.PlayerBuildEvent)
	log.WithField("evt", evt).Info("Received PlayerBuild event")

	// check that the entity exists
	if ent, ok := gs.entities[evt.Id]; ok {
		p := ent.(*entities.Player)

		// only engineers can build
		if p.Type() != game.EngineerEntity {
			gs.game.clients.Kick(evt.Id, "illegal action: only engineers can build!")
			return
		}

		// clip building center to center of a game square unit
		dst := math.FromInts(int(evt.Xpos), int(evt.Ypos)).
			Add(math.Vec2{0.5, 0.5})

		// create the building
		building := entities.NewBasicBuilding()
		gs.AddEntity(building)

		// set player action
		p.Build(evt.Type, dst)
		// plan movement
		gs.fillMovementRequest(p, dst)
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
 * AddEntity adds specifies entity to the game state.
 *
 * It also assigns it a unique Id
 */
func (gs *gamestate) AddEntity(ent game.Entity) uint32 {
	id := gs.allocEntityId()
	gs.entities[id] = ent
	ent.SetId(id)
	return id
}

func (gs *gamestate) MapData() *resource.MapData {
	return gs.md
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

func (gs *gamestate) NearestEntity(pos math.Vec2, f game.EntityFilter) (game.Entity, float32) {
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
