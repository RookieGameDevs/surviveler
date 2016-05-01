package game

import (
	log "github.com/Sirupsen/logrus"
	"runtime"
	"time"
)

/*
 * loop is the main game loop, it fetches messages from a channel, processes
 * them immediately.
 */
func (g *Game) loop() {

	// will tick when it's time to send the gamestate to the clients
	tickChan := time.NewTicker(time.Millisecond * 100).C

	go func() {

		quit := false
		for !quit {
			select {
			case <-g.loopCloseChan:
				// quit immediately
				quit = true
			case msg := <-g.msgChan:
				// process message
				log.WithField("msg", msg).Debug("Message received")
			case <-tickChan:
				// send state ticker
				log.WithField("time", MakeTimestamp()).Debug("Send state Ticker")
			default:
				// let the world spin
				runtime.Gosched()
			}
		}
		log.Debug("Game loop just ended")
	}()
}
