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
	"server/math"
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
	TnTeleportEntityId
)

type TnTeleportEntity struct {
	Id   int       // id of the entity to teleport
	Dest math.Vec2 // destination
}

/*
 * setTelnetHandlers sets the handlers for game related telnet commands. Game
 * related telnet commands use a channel to signal the game loop,  */
func (g *Game) setTelnetHandlers() {
	func() {
		// register 'gamestate' command
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
	}()

	func() {
		// register 'teleport' command
		cmd := protocol.NewTelnetCmd("teleport")
		cmd.Descr = "teleport an entity onto a specific -walkable- point"
		entityId := cmd.Parms.Int("id", -1, "entity id (integer)")
		pos := math.Vec2{}
		cmd.Parms.Var(&pos, "dest", "destination (Vec2, example 3.12,4.56)")
		cmd.Handler = func(w io.Writer) {
			req := TelnetRequest{
				Type:    TnTeleportEntityId,
				Writer:  w,
				Content: &TnTeleportEntity{*entityId, pos},
			}
			g.telnetChan <- req
		}
		g.telnet.RegisterCommand(cmd)
	}()
}

/*
 * telnetHandler is exclusively called from the game loop, when it has been
 * signaled about an incoming telnet request. This guaranty implies that nobody
 * else has access to the game state. However, no blocking call should ever be
 * performed inside this handler.
 */
func (g *Game) telnetHandler(msg TelnetRequest, gs *GameState) {
	log.WithField("msg", msg).Info("Received telnet game message")
	switch msg.Type {
	case TnGameStateId:
		if gsMsg := gs.pack(); gsMsg != nil {
			io.WriteString(msg.Writer, fmt.Sprintf("%v\n", *gsMsg))
		}
	case TnTeleportEntityId:
		teleport := msg.Content.(*TnTeleportEntity)
		log.WithField("teleport", teleport).Info("Received teleport")

		// TODO: implement instant telnet teleportation
		// be aware of the folowing though:
		// just setting player pos won't work if any pathfinding is in progress
		// what to do?
		// cancel the pathfinding? but also set the entity state to idle?
		// it's ok if it's a player...
		// but what will happen when it will be a zombie?
	}
}
