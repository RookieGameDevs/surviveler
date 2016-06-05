/*
 * Surviveler game package
 * game related telnet commands
 */
package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"github.com/urfave/cli"
	"io"
	"server/math"
)

/*
 * TelnetRequest represents the type and content of a telnet request, and a way to
 * reply to it
 */
type TelnetRequest struct {
	Type    uint32
	Context *cli.Context
	Content Contexter
}

const (
	TnGameStateId uint32 = 0 + iota
	TnMoveEntityId
	TnTeleportEntityId
)

/*
 * Contexter is the interface implemented by objects that can unserialize
 * themselves from a cli context
 */
type Contexter interface {
	FromContext(c *cli.Context) error
}

type TnGameState struct {
	// empty
}

type TnMoveEntity struct {
	Id   uint32    // entity id
	Dest math.Vec2 // destination
}

type TnTeleportEntity TnMoveEntity

func (req *TnGameState) FromContext(c *cli.Context) error {
	return nil
}

func (req *TnMoveEntity) FromContext(c *cli.Context) error {
	fmt.Println("In TnMoveEntity")
	Id := c.Int("id")
	if Id < 0 {
		return fmt.Errorf("invalid id")
	}
	req.Id = uint32(Id)
	if err := req.Dest.Set(c.String("pos")); err != nil {
		return fmt.Errorf("invalid position vector: %s", c.String("pos"))
	}
	return nil
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
	createHandler := func(req TelnetRequest) cli.ActionFunc {
		return func(c *cli.Context) error {
			// bind the context to the request
			req.Context = c
			// parse cli args into req structure fields
			if err := req.Content.FromContext(c); err != nil {
				io.WriteString(c.App.Writer, fmt.Sprintf("error: %v\n", err))
				return nil
			}
			// send the request
			g.telnetChan <- req
			// now wait that til' it has been executed
			if err := <-g.telnetDoneChan; err != nil {
				io.WriteString(c.App.Writer, fmt.Sprintf("error: %v\n", err))
			}
			return nil
		}
	}

	func() {
		// register 'gamestate' command
		cmd := cli.Command{
			Name:  "gamestate",
			Usage: "shows current gamestate",
			Action: createHandler(
				TelnetRequest{Type: TnGameStateId, Content: &TnGameState{}}),
		}
		g.telnet.RegisterCommand(&cmd)
	}()

	func() {
		// register 'move' command
		cmd := cli.Command{
			Name:  "move",
			Usage: "move an entity onto a specific -walkable- 2D point",
			Flags: []cli.Flag{
				cli.IntFlag{Name: "id", Usage: "entity id", Value: -1},
				cli.StringFlag{Name: "pos", Usage: "2D vector, ex: 3,4.5"},
			},
			Action: createHandler(
				TelnetRequest{Type: TnMoveEntityId, Content: &TnMoveEntity{}}),
		}
		g.telnet.RegisterCommand(&cmd)
	}()

	//func() {
	//// register 'teleport' command
	//cmd := protocol.NewTelnetCmd("teleport")
	//cmd.Descr = "teleport an entity onto a specific -walkable- point"
	//entityId := cmd.Parms.Int("id", -1, "entity id (integer)")
	//pos := math.Vec2{}
	//cmd.Parms.Var(&pos, "dest", "destination (Vec2, ex: 3.12,4.56)")
	//cmd.Handler = createHandler(
	//TelnetRequest{
	//Type:    TnTeleportEntityId,
	//Content: &TnTeleportEntity{*entityId, pos},
	//})
	//g.telnet.RegisterCommand(cmd)
	//}()
}

/*
 * telnetHandler is the unique handlers for game related telnet request.
 *
 * Because it is exclusively called from inside a select case of the game loop,
 * it is safe to read/write the gamestate here. However, every call should only
 * perform non-blocking only operations, as the game logic is **not** updated
 * as long as the handler is in execution.
 */
func (g *Game) telnetHandler(msg TelnetRequest, gs *GameState) error {
	log.WithField("msg", msg).Info("Handling a telnet game message")
	switch msg.Type {
	case TnGameStateId:
		if gsMsg := gs.pack(); gsMsg != nil {
			io.WriteString(msg.Context.App.Writer, fmt.Sprintf("%v\n", *gsMsg))
			return nil
		} else {
			return fmt.Errorf("no gamestate to show\n")
		}
	case TnMoveEntityId:
		move := msg.Content.(*TnMoveEntity)
		if player, ok := gs.players[move.Id]; ok {

			io.WriteString(msg.Context.App.Writer, fmt.Sprintf("moved player %v\n", *player))
			io.WriteString(msg.Context.App.Writer, fmt.Sprintf("Handling move %v\n", *move))
		} else {
			return fmt.Errorf("unknown entity id: %v", move.Id)
		}
		return nil
	case TnTeleportEntityId:
		teleport := msg.Content.(*TnTeleportEntity)

		// TODO: implement instant telnet teleportation
		// be aware of the folowing though:
		// just setting player pos won't work if any pathfinding is in progress
		// what to do?
		// cancel the pathfinding? but also set the entity state to idle?
		// it's ok if it's a player...
		// but what will happen when it will be a zombie?
	}
	return fmt.Errorf("Unknow telnet message id")
}
