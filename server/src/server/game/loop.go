package game

import (
	log "github.com/Sirupsen/logrus"
	"runtime"
	"server/game/entity"
	"time"
)

type GameState struct {
	players map[uint16]*entity.Player
}

/*
 * loop is the main game loop, it fetches messages from a channel, processes
 * them immediately.
 */
func (g *Game) loop() {

	// will tick when it's time to send the gamestate to the clients
	sendTickChan := time.NewTicker(time.Millisecond * 100).C

	// will tick when it's time to update the game
	tickChan := time.NewTicker(time.Millisecond * 10).C

	// encapsulate the game state here, as it should not be accessed nor modified
	// from outside the game loop
	gs := GameState{}
	gs.players = make(map[uint16]*entity.Player)

	go func() {
		for {
			select {

			case <-g.loopCloseChan:

				log.Debug("Game loop just ended")
				return

			case msg := <-g.msgChan:

				// process client message
				log.WithField("msg", msg).Debug("Message received")
				switch msg.Type {
				case NewPlayerId:
					// we have a new player
					nextId := uint16(len(gs.players))
					gs.players[nextId] = new(entity.Player)
				}

			case <-sendTickChan:

				g.sendGameState(&gs)

			case <-tickChan:

				// tick game
				for _, ent := range gs.players {
					var dt float32
					// TODO: compute delta time
					ent.Update(dt)
				}

			default:

				// let the world spin
				runtime.Gosched()
			}
		}
	}()
}
