/*
 * Surviveler
 * game entry point
 */
package main

import (
	"server/game"
)

func main() {
	// game setup
	var surviveler game.Game
	if surviveler.Setup() {
		// start the game
		surviveler.Start()
	}
}
