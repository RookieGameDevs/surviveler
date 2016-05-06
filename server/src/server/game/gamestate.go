/*
 * Surviveler game package
 * game state structure
 */

package game

import (
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
