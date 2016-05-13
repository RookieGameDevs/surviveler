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
	"server/game/protocol"
	"server/math"
	"time"
)

/*
 * GameState is the structure that contains all the complete game state
 */
type GameState struct {
	players map[uint16]*entity.Player
}

func NewGameState() GameState {

	return GameState{
		players: make(map[uint16]*entity.Player),
	}
}

/*
 * pack transforms the current game state into a GameStateMsg,
 * ready to be sent to every connected client
 */
func (gs GameState) pack() (*protocol.Message, error) {

	if len(gs.players) == 0 {
		// nothing to do
		return nil, nil
	}

	// fill the GameStateMsg
	var gsMsg messages.GameStateMsg
	gsMsg.Tstamp = time.Now().UnixNano() / int64(time.Millisecond)
	gsMsg.Entities = make(map[uint16]interface{})
	for id, ent := range gs.players {
		gsMsg.Entities[id] = ent.GetState()
	}

	// wrap the GameStateMsg into a generic Message
	msg, err := protocol.NewMessage(messages.GameStateId, gsMsg)
	if err != nil {
		log.WithField("err", err).Fatal("Couldn't pack game state")
		return nil, err
	}
	log.WithField("msg", gsMsg).Debug("Packed game state")
	return msg, nil
}

func (gs *GameState) onAddPlayer(msg interface{}, clientId uint16) error {
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", clientId).Info("we have a new player")
	gs.players[clientId] = entity.NewPlayer(0, 0, 2)
	return nil
}

func (gs *GameState) onDelPlayer(msg interface{}, clientId uint16) error {
	// one player less, remove him from the map
	log.WithField("clientId", clientId).Info("we have one less player")
	delete(gs.players, clientId)
	return nil
}

func (gs *GameState) onMovePlayer(msg interface{}, clientId uint16) error {
	move := msg.(messages.MoveMsg)
	log.WithFields(log.Fields{"clientId": clientId, "msg": move}).Info("onMovePlayer")
	if p, ok := gs.players[clientId]; ok {
		p.Move(math.Vec2{move.Xpos, move.Ypos})
	} else {
		return fmt.Errorf("Client Id not found: %v", clientId)
	}
	return nil
}
