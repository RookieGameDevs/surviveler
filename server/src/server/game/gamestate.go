package game

import (
	log "github.com/Sirupsen/logrus"
)

/*
 * sendGameState sends the whole game state to all the connected clients
 */
func (g *Game) sendGameState(gs GameState) {

	// create a GameStateMsg from the game state
	gsMsg := GameStateMsg{
		Tstamp: MakeTimestamp(),
		Xpos:   gs.players[0].XPos,
		Ypos:   gs.players[0].YPos,
		Action: ActionMsg{
			ActionType:   0,
			TargetTstamp: MakeTimestamp(),
			Xpos:         gs.players[0].XPos,
			Ypos:         gs.players[0].YPos,
		},
	}

	msg, err := NewMessage(MsgType(GameStateId), gsMsg)
	if err != nil {
		log.WithField("err", err).Debug("Error creating gamestate msg")
		return
	}
	log.WithField("msg", msg).Debug("Sending gamestate msg")
	g.clients.sendAll(msg)
}
