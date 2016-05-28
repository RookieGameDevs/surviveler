/*
 * Surviveler game package
 * game state structure
 */

package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"server/game/entity"
	"server/game/messages"
	"server/game/resource"
	"server/math"
	"time"
)

/*
 * GameState is the structure that contains all the complete game state
 */
type GameState struct {
	players    map[uint32]*entity.Player
	World      *World
	Pathfinder Pathfinder
}

func newGameState() GameState {
	return GameState{
		players: make(map[uint32]*entity.Player),
	}
}

func (gs *GameState) init(pkg resource.SurvivelerPackage) error {
	var err error
	gs.World, err = NewWorld(pkg)
	gs.Pathfinder.World = gs.World
	return err
}

/*
 * pack transforms the current game state into a GameStateMsg
 */
func (gs GameState) pack() *messages.GameStateMsg {
	if len(gs.players) == 0 {
		// nothing to do
		return nil
	}

	// fill the GameStateMsg
	gsMsg := new(messages.GameStateMsg)
	gsMsg.Tstamp = time.Now().UnixNano() / int64(time.Millisecond)
	gsMsg.Entities = make(map[uint32]interface{})
	for id, ent := range gs.players {
		gsMsg.Entities[id] = ent.GetState()
	}
	return gsMsg
}

/*
 * onPlayerJoined handles a JoinedMsg by instanting a new player entity
 */
func (gs *GameState) onPlayerJoined(msg interface{}, clientId uint32) error {
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", clientId).Info("we have a new player")
	gs.players[clientId] = entity.NewPlayer(1, 1, 2)
	return nil
}

/*
 * onPlayerLeft handles a LeaveMsg by removing an entity
 */
func (gs *GameState) onPlayerLeft(msg interface{}, clientId uint32) error {
	// one player less, remove him from the map
	log.WithField("clientId", clientId).Info("we have one less player")
	delete(gs.players, clientId)
	return nil
}

/*
 * onMovePlayer handles a MoveMsg by setting the final destination of an entity
 */
func (gs *GameState) onMovePlayer(msg interface{}, clientId uint32) error {
	move := msg.(messages.MoveMsg)
	log.WithFields(log.Fields{"clientId": clientId, "msg": move}).Info("onMovePlayer")

	if player, ok := gs.players[clientId]; ok {

		// compute pathfinding
		dst := math.Vec2{move.Xpos, move.Ypos}
		if path, _, found := gs.Pathfinder.FindPlayerPath(player, player.Pos, dst); found {
			if len(path) >= 2 {
				log.WithFields(log.Fields{"path": path, "clientId": clientId}).
					Info("PlayerPathfinder found a path")
				player.SetPath(path)
			} else {
				// TODO: probably better to manage this somewhere else (maybe even on the client side?)
				log.WithFields(log.Fields{"path": path, "clientId": clientId}).
					Warn("PlayerPathfinder: destination cell too close")
			}
		} else {
			log.WithFields(log.Fields{"clientId": clientId, "pos": player.Pos, "dst": dst}).
				Warn("Pathfinder failed to find path")
		}
	} else {
		return fmt.Errorf("Client Id not found: %v", clientId)
	}
	return nil
}
