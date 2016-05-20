/*
 * Surviveler game package
 * game related telnet commands
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
 * related telnet commands use a channel to signal the game loop,  */
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

/*
 * telnetHandler is exclusively called from the game loop, when it has been
 * signaled about an incoming telnet request. This guaranty implies that nobody
 * else has access to the game state. However, no blocking call should ever be
 * performed inside this handler.
 */
func (g *Game) telnetHandler(msg TelnetRequest, gs *GameState) {
	log.WithField("msg", msg).Info("Received telnet game messages")
	switch msg.Type {
	case TnGameStateId:
		if gsMsg := gs.pack(); gsMsg != nil {
			io.WriteString(msg.Writer, fmt.Sprintf("%v\n", *gsMsg))
		}
	}
}
