/*
 * Surviveler game package
 * game related telnet request
 */
package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"io"
	"server/game/protocol"
)

/*
 * TelnetRequest represents the type and content of a telnet request, and a way to
 * reply to it
 */
type TelnetRequest struct {
	Type    uint32
	Content interface{}
	Writer  io.Writer
}

const (
	TnGameStateId uint32 = 0 + iota
)

/*
 * setTelnetHandlers sets the handlers for game related telnet commands. Game
 * related telnet requests use a channel to signal the game loop, thus
 * guaranteeing us that the functions handling those requests won't be compete
 * with others functions having access to the game stae. Therefore, those
 * handlers can read and modify the game state without problem.
 */
func (g *Game) setTelnetHandlers() {
	cmd := protocol.NewTelnetCmd("gamestate")
	cmd.Descr = "prints the gamestate"
	cmd.Handler = func(w io.Writer) {
		req := TelnetRequest{
			Type:   TnGameStateId,
			Writer: w,
		}
		g.telnetChan <- req
	}
	g.telnet.RegisterCommand(cmd)
}

func (g *Game) telnetHandler(msg TelnetRequest, gs *GameState) {
	log.WithField("msg", msg).Info("Received telnet game messages")

	switch msg.Type {
	case TnGameStateId:
		if gsMsg := gs.pack(); gsMsg != nil {
			io.WriteString(msg.Writer, fmt.Sprintf("%v\n", *gsMsg))
		}
	}
}
