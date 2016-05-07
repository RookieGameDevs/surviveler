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

	// create a GameStateMsg from the game state
	if len(gs.players) == 0 {
		log.Debug("sendGameState: nothing to pack, 0 players")
		return nil, nil
	}

	var ent0 entity.Player
	ent0 = *gs.players[0]

	gsMsg := messages.GameStateMsg{
		Tstamp: MakeTimestamp(),
		Xpos:   ent0.XPos,
		Ypos:   ent0.YPos,
		Action: messages.ActionMsg{
			ActionType:   0,
			TargetTstamp: MakeTimestamp(),
			Xpos:         ent0.XPos,
			Ypos:         ent0.YPos,
		},
	}

	// wrap the specialized GameStateMsg into a generic Message
	msg, err := protocol.NewMessage(messages.GameStateId, gsMsg)
	if err != nil {
		log.WithField("err", err).Fatal("Couldn't create Message from gamestate")
		return nil, err
	}

	return msg, nil
}

func (gs *GameState) onAddPlayer(msg interface{}, clientId uint16) error {
	// we have a new player, his id will be its unique connection id
	log.WithField("clientId", clientId).Info("we have a new player")
	gs.players[clientId] = new(entity.Player)
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
	log.WithFields(log.WithFields{
		"clientId": clientId,
		"msg":      move,
	}).Info("handling a MoveMsg")

	var p *entity.Player
	var ok bool
	if p, ok = gs.players[clientId]; !ok {
		return fmt.Errorf("player with this clientId (%v) doesn't exist", clientId)
	}
	p.SetDestination(moveMsg.Xpos, moveMsg.Ypos)

	return nil
}
