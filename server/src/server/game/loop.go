package game

import (
	log "github.com/Sirupsen/logrus"
	"runtime"
	"server/game/entity"
	"server/game/protocol"
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
				case protocol.AddPlayerId:
					// we have a new player, assign her the unique connection id
					gs.players[msg.ClientId] = new(entity.Player)
				case protocol.DelPlayerId:
					// one less player
					log.WithField("id", msg.ClientId).Info("Removing player from the game state")
					delete(gs.players, msg.ClientId)
				}

			case <-sendTickChan:

				// pack the gamestate into a message
				var msg *protocol.Message
				var err error
				if msg, err = gs.pack(); err != nil {
					log.WithField("err", err).Error("Couldn't pack the gamestate")
					quit = true
				}
				if msg != nil {
					log.WithField("msg", msg).Debug("Sending gamestate msg")
					g.server.Broadcast(msg)
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
