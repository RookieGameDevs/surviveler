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
 * registerTelnetHandlers declares and registers the game-related telnet
 * handlers.
 *
 * By *game-related* telnet handler, it is intented a telnet handler that is to
 * be treated by the game loop. The telnet handlers do nothing more than
 * forwarding the TelnetRequest to a specific channel, read exclusively in the
 * game loop, that will trigger the final handler (i.e the actual handler of the
 * request)
 */
func (g *Game) registerTelnetHandlers() {
	// function that creates and returns telnet handlers on the fly
	createHandler := func(req TelnetRequest) protocol.TelnetHandlerFunc {
		return func(w io.Writer) {
			req.Writer = w
			g.telnetChan <- req
		}
	}

	func() {
		// register 'gamestate' command
		cmd := protocol.NewTelnetCmd("gamestate")
		cmd.Descr = "prints the gamestate"
		cmd.Handler = createHandler(TelnetRequest{Type: TnGameStateId})
		g.telnet.RegisterCommand(cmd)
	}()

	func() {
		// register 'teleport' command
		cmd := protocol.NewTelnetCmd("teleport")
		cmd.Descr = "teleport an entity onto a specific -walkable- point"
		entityId := cmd.Parms.Int("id", -1, "entity id (integer)")
		pos := math.Vec2{}
		cmd.Parms.Var(&pos, "dest", "destination (Vec2, ex: 3.12,4.56)")
		cmd.Handler = createHandler(
			TelnetRequest{
				Type:    TnTeleportEntityId,
				Content: &TnTeleportEntity{*entityId, pos},
			})
		g.telnet.RegisterCommand(cmd)
	}()
}

/*
 * telnetHandler is the unique handlers for game related telnet request.
 *
 * Because it is exclusively called from inside a select case of the game loop,
 * it is safe to read/write the gamestate here. However, every call should only
 * perform non-blocking only operations, as the game logic is **not** updated
 * as long as the handler is in execution.
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
