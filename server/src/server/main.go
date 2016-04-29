package main

import (
	"fmt"
	"os"
	"os/signal"
	"server/game"
	"syscall"
)

func main() {
	// game setup
	cfg := game.GameCfg{
		Port: "1234",
	}

	surviveler := new(game.Game)
	surviveler.Setup(cfg)

	// start the game
	go surviveler.Start()

	// be notified of termination signals
	chSig := make(chan os.Signal)
	signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)

	// wait for termination signals
	fmt.Println("Received signal: ", <-chSig)
	surviveler.Stop()
}
