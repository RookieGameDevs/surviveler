package game

import (
	"fmt"
	"time"
)

/*
 * loop is the main game loop
 */
func (g *Game) loop() {

	for range g.ticker.C {
		time.Sleep(2 * time.Millisecond)

		// handles player actions

		// send game state to connected clients

	}
	fmt.Println("game loop just ended")
}
