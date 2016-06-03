/*
 * Surviveler game package
 * game state structure
 */

package game

import (
	log "github.com/Sirupsen/logrus"
	"server/game/entity"
	"server/game/messages"
	"server/game/resource"
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

func newGameState() *GameState {
	return &GameState{
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
	log.WithField("clientId", clientId).Info("We have one more player")
	gs.players[clientId] = entity.NewPlayer(1, 1, 3)
	return nil
}

/*
 * onPlayerLeft handles a LeaveMsg by removing an entity
 */
func (gs *GameState) onPlayerLeft(msg interface{}, clientId uint32) error {
	// one player less, remove him from the map
	log.WithField("clientId", clientId).Info("We have one less player")
	delete(gs.players, clientId)
	return nil
}

/*
 * onMovementRequestResult handles a MovementRequestResultMsg
 */
func (gs *GameState) onMovementRequestResult(msg interface{}, clientId uint32) error {
	mvtReqRes := msg.(messages.MovementRequestResultMsg)
	log.WithField("res", mvtReqRes).Info("Received a MovementRequestResultMsg")

	// check that the entity exists
	if player, ok := gs.players[mvtReqRes.EntityId]; ok {
		player.SetPath(mvtReqRes.Path)
	}
	return nil
}
