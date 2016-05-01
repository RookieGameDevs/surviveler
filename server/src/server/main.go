package main

import (
	"server/game"
)

func main() {
	// game setup
	cfg := game.GameCfg{
		Port: "1234",
	}

	surviveler := new(game.Game)
	surviveler.Setup(cfg)

	// start the game
	surviveler.Start()
}
