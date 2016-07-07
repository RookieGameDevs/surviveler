/*
 * Surviveler game package
 * game related telnet commands
 */
package surviveler

import (
	"errors"
	"fmt"
	log "github.com/Sirupsen/logrus"
	"github.com/urfave/cli"
	"io"
	"server/game/events"
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
	TnBuildId
	TnRepairId
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

type TnBuild struct {
	Id   uint32    // entity id
	Type uint8     // building type
	Pos  math.Vec2 // building position
}

type TnRepair struct {
	Id         uint32 // entity id
	BuildingId uint32 // building id
}

func (req *TnGameState) FromContext(c *cli.Context) error {
	return nil
}

func (req *TnMoveEntity) FromContext(c *cli.Context) error {
	fmt.Println("In TnMoveEntity")
	Id := c.Int("id")
	if Id < 0 {
		return fmt.Errorf("invalid id")
	} else {
		req.Id = uint32(Id)
	}

	if err := req.Dest.Set(c.String("pos")); err != nil {
		return fmt.Errorf("invalid position vector: %s", c.String("pos"))
	}
	return nil
}

func (req *TnTeleportEntity) FromContext(c *cli.Context) error {
	fmt.Println("In TnTeleportEntity")
	Id := c.Int("id")
	if Id < 0 {
		return fmt.Errorf("invalid id")
	} else {
		req.Id = uint32(Id)
	}

	if err := req.Dest.Set(c.String("pos")); err != nil {
		return fmt.Errorf("invalid position vector: %s", c.String("pos"))
	}
	return nil
}

func (req *TnBuild) FromContext(c *cli.Context) error {
	fmt.Println("In TnBuild")
	Id := c.Int("id")
	if Id < 0 {
		return fmt.Errorf("invalid id")
	} else {
		req.Id = uint32(Id)
	}

	if err := req.Pos.Set(c.String("pos")); err != nil {
		return fmt.Errorf("invalid position vector: %s", c.String("pos"))
	}

	Type := c.Int("type")
	if Type < 0 {
		return fmt.Errorf("invalid id")
	} else {
		req.Type = uint8(Type)
	}
	return nil
}

func (req *TnRepair) FromContext(c *cli.Context) error {
	fmt.Println("In TnRepair")
	Id := c.Int("id")
	if Id < 0 {
		return fmt.Errorf("invalid id")
	} else {
		req.Id = uint32(Id)
	}

	BId := c.Int("bid")
	if BId < 0 {
		return fmt.Errorf("invalid building id")
	} else {
		req.BuildingId = uint32(BId)
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
func (g *survivelerGame) registerTelnetHandlers() {
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
			g.telnetReq <- req
			// now wait that til' it has been executed
			// by convention, the handler should return an error in case of failure
			// and nil in case of success; it means that any success report should
			// be done from the handler
			if err := <-g.telnetDone; err == nil {
				io.WriteString(c.App.Writer, "success!\n")
			} else {
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

	func() {
		// register 'teleport' command
		cmd := cli.Command{
			Name:  "teleport",
			Usage: "teleport an entity onto a specific -walkable- 2D point",
			Flags: []cli.Flag{
				cli.IntFlag{Name: "id", Usage: "entity id", Value: -1},
				cli.StringFlag{Name: "pos", Usage: "2D vector, ex: 3,4.5"},
			},
			Action: createHandler(
				TelnetRequest{Type: TnTeleportEntityId, Content: &TnTeleportEntity{}}),
		}
		g.telnet.RegisterCommand(&cmd)
	}()

	func() {
		// register 'build' command
		cmd := cli.Command{
			Name:  "build",
			Usage: "make a player create a building of given type at a specific -walkable- 2D point",
			Flags: []cli.Flag{
				cli.IntFlag{Name: "id", Usage: "entity id", Value: -1},
				cli.StringFlag{Name: "type", Usage: "building type"},
				cli.StringFlag{Name: "pos", Usage: "2D vector, ex: 3,4.5"},
			},
			Action: createHandler(
				TelnetRequest{Type: TnBuildId, Content: &TnBuild{}}),
		}
		g.telnet.RegisterCommand(&cmd)
	}()

	func() {
		// register 'repair' command
		cmd := cli.Command{
			Name:  "repair",
			Usage: "make a player repair a buliding, that is partially destroyed or unfinished",
			Flags: []cli.Flag{
				cli.IntFlag{Name: "id", Usage: "entity id", Value: -1},
				cli.IntFlag{Name: "bid", Usage: "building id", Value: -1},
			},
			Action: createHandler(
				TelnetRequest{Type: TnRepairId, Content: &TnRepair{}}),
		}
		g.telnet.RegisterCommand(&cmd)
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
func (g *survivelerGame) telnetHandler(msg TelnetRequest) error {
	log.WithField("msg", msg).Info("Handling a telnet game message")

	switch msg.Type {

	case TnGameStateId:

		if gsMsg := g.state.pack(); gsMsg != nil {
			io.WriteString(msg.Context.App.Writer, fmt.Sprintf("%v\n", *gsMsg))
			return nil
		} else {
			return errors.New("no gamestate to show")
		}

	case TnMoveEntityId:

		move := msg.Content.(*TnMoveEntity)
		if err := g.state.isPlayer(move.Id); err != nil {
			return err
		}

		// emit a PlayerMove event
		evt := events.NewEvent(events.PlayerMove,
			events.PlayerMoveEvent{
				Id:   move.Id,
				Xpos: float32(move.Dest[0]),
				Ypos: float32(move.Dest[1]),
			})
		g.PostEvent(evt)
		return nil

	case TnTeleportEntityId:

		teleport := msg.Content.(*TnTeleportEntity)
		return fmt.Errorf("not implemented! but teleport received: %v", *teleport)
		// TODO: implement instant telnet teleportation
		// be aware of the folowing though:
		// just setting player pos won't work if any pathfinding is in progress
		// what to do?
		// cancel the pathfinding? but also set the entity state to idle?
		// it's ok if it's a player...
		// but what will happen when it will be a zombie?

	case TnBuildId:

		build := msg.Content.(*TnBuild)
		if err := g.state.isPlayer(build.Id); err != nil {
			return err
		}
		// TODO: hard-coded building type check for now
		if build.Type != 0 {
			return fmt.Errorf("unknown building type: %v", build.Type)
		}
		// emit a PlayerBuild event
		evt := events.NewEvent(events.PlayerBuild, events.PlayerBuildEvent{
			Id:   build.Id,
			Xpos: float32(build.Pos[0]),
			Ypos: float32(build.Pos[1]),
			Type: uint8(build.Type),
		})
		g.PostEvent(evt)
		return nil

	case TnRepairId:

		repair := msg.Content.(*TnRepair)
		if err := g.state.isPlayer(repair.Id); err != nil {
			return err
		}
		if err := g.state.isBuilding(repair.BuildingId); err != nil {
			return err
		}
		// emit a PlayerRepair event
		evt := events.NewEvent(events.PlayerRepair, events.PlayerRepairEvent{
			Id:         repair.Id,
			BuildingId: repair.BuildingId,
		})
		g.PostEvent(evt)
		return nil

	}
	return errors.New("Unknow telnet message id")
}
