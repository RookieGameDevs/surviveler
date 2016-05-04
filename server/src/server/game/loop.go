package game

import (
	log "github.com/Sirupsen/logrus"
	"runtime"
	"server/game/entity"
	"time"
)

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

	// loop local stop condition
	quit := false

	go func() {
		for !quit {
			select {

			case <-g.loopCloseChan:
				quit = true

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

				// pack the gamestate into a message
				var msg *Message
				var err error
				if msg, err = gs.pack(); err != nil {
					log.WithField("err", err).Error("Couldn't pack the gamestate")
					quit = true
				}
				if msg != nil {
					log.WithField("msg", msg).Debug("Sending gamestate msg")
					g.clients.sendAll(msg)
				}

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

		log.Info("Game just stopped ticking")
	}()
}
