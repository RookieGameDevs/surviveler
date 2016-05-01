package game

import (
	log "github.com/Sirupsen/logrus"
	"runtime"
)

/*
 * loop is the main game loop
 */
func (g *Game) loop() {

	go func() {

		quit := false
		for !quit {
			select {
			case <-g.loopCloseChan:
				// quit immediately
				quit = true
			case msg := <-g.msgChan:
				log.WithField("msg", msg).Debug("Message received")
			default:
				// let the world spin
				runtime.Gosched()
			}
		}
		log.Debug("Game loop just ended")
	}()
}
