/*
 * Surviveler game package
 * game state structure
 */

package game

import (
	"errors"
	"fmt"
	"image"
	"server/game/entity"
	msg "server/game/messages"
	"server/game/resource"
	"time"

	log "github.com/Sirupsen/logrus"
)

/*
 * GameState is the structure that contains all the complete game state
 */
type GameState struct {
	game       *Game
	gameTime   int16
	players    map[uint32]*entity.Player
	zombies    map[uint32]*entity.Zombie
	World      *World
	pathfinder Pathfinder
	md         *resource.MapData
	director   AIDirector
}

func newGameState(g *Game) *GameState {
	return &GameState{
		game:    g,
		players: make(map[uint32]*entity.Player),
		zombies: make(map[uint32]*entity.Zombie),
	}
}

/*
 * init loads configuration from an assets package and initializes various game
 * state sub-structures
 */
func (gs *GameState) init(pkg resource.SurvivelerPackage) error {
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
				if gs.World, err = NewWorld(worldBmp, gs.md.ScaleFactor); err == nil {
					gs.pathfinder.World = gs.World
					if err = gs.validateWorld(); err == nil {
						gs.director.init(gs)
					}
				}
			}
		}
	}
	return err
}

/*
 * validateWorld performs some logical and semantic checks on the loaded world
 */
func (gs GameState) validateWorld() error {
	spawnPoints := gs.md.AIKeypoints.Spawn
	// validate player spawn point
	pt := gs.World.TileFromWorldVec(spawnPoints.Player)
	if pt == nil {
		return fmt.Errorf(
			"Player spawn point is out of bounds (%#v)",
			spawnPoints.Player)
	}
	if pt.Kind&KindWalkable == 0 {
		return fmt.Errorf(
			"Player spawn point is located on a non-walkable point: (%#v)",
			*pt)
	}
	// validate enemies spawn points
	if len(spawnPoints.Enemies) == 0 {
		return errors.New("At least one enemy spawn point must be defined")
	}
	for i := range spawnPoints.Enemies {
		zt := gs.World.TileFromWorldVec(spawnPoints.Enemies[i])
		if zt == nil {
			return fmt.Errorf(
				"A Zombie spawn point is out of bounds: (%#v)",
				spawnPoints.Enemies[i])
		}
		if zt.Kind&KindWalkable == 0 {
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
func (gs GameState) pack() *msg.GameStateMsg {
	// fill the GameStateMsg
	gsMsg := new(msg.GameStateMsg)
	gsMsg.Tstamp = time.Now().UnixNano() / int64(time.Millisecond)
	gsMsg.Time = gs.gameTime
	gsMsg.Entities = make(map[uint32]interface{})
	for id, plr := range gs.players {
		gsMsg.Entities[id] = plr.GetState()
	}
	for id, zom := range gs.zombies {
		gsMsg.Entities[id] = zom.GetState()
	}
	return gsMsg
}

/*
 * onPlayerJoined handles a JoinedMsg by instanting a new player entity
 */
func (gs *GameState) onPlayerJoined(imsg interface{}, clientId uint32) error {
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", clientId).Info("We have one more player")
	gs.players[clientId] = entity.NewPlayer(gs.md.AIKeypoints.Spawn.Player, 3)
	return nil
}

/*
 * onPlayerLeft handles a LeaveMsg by removing an entity
 */
func (gs *GameState) onPlayerLeft(imsg interface{}, clientId uint32) error {
	// one player less, remove him from the map
	log.WithField("clientId", clientId).Info("We have one less player")
	delete(gs.players, clientId)
	return nil
}

/*
 * onMovementRequestResult handles a MovementRequestResultMsg
 *
 * MovementRequestResult are server-side messages only emitted by the movement
 * planner to signal that the pathfinder has finished to compute a path
 */
func (gs *GameState) onMovementRequestResult(imsg interface{}, clientId uint32) error {
	mvtReqRes := imsg.(msg.MovementRequestResultMsg)
	log.WithField("res", mvtReqRes).Info("Received a MovementRequestResultMsg")

	// check that the entity exists
	if player, ok := gs.players[mvtReqRes.EntityId]; ok {
		player.SetPath(mvtReqRes.Path)
	}
	return nil
}
