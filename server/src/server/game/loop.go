package game

import (
	"fmt"
	"time"
)

func (g *Game) loop() {

	for range g.ticker.C {
		time.Sleep(2 * time.Millisecond)
	}
	fmt.Println("game loop just ended")
}
