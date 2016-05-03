package game

import (
	log "github.com/Sirupsen/logrus"
	"server/game/entity"
)

/*
 * sendGameState sends the whole game state to all the connected clients
 */
func (g *Game) sendGameState(gs *GameState) {

	// create a GameStateMsg from the game state
	if len(gs.players) == 0 {
		log.Info("sendGameState: nothing to send, 0 players")
		return
	}
	var ent0 entity.Player
	ent0 = *gs.players[0]

	gsMsg := GameStateMsg{
		Tstamp: MakeTimestamp(),
		Xpos:   ent0.XPos,
		Ypos:   ent0.YPos,
		Action: ActionMsg{
			ActionType:   0,
			TargetTstamp: MakeTimestamp(),
			Xpos:         ent0.XPos,
			Ypos:         ent0.YPos,
		},
	}

	msg, err := NewMessage(MsgType(GameStateId), gsMsg)
	if err != nil {
		log.WithField("err", err).Debug("Error creating gamestate msg")
		return
	}
	log.WithField("msg", gsMsg).Debug("Sending gamestate msg")
	g.clients.sendAll(msg)
}
