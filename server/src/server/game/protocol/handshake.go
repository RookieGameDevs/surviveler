/*
 * Surviveler protocol package
 * server implementation: handshake
 */
package protocol

import (
	"fmt"
	"io"
	"server/game/messages"
	"server/network"

	"github.com/urfave/cli"
)

type (
	// AfterJoinHandler is the function called after a successfull JOIN.
	AfterJoinHandler func(ID uint32, playerType uint8)

	// AfterLeaveHandler is the function called after an effective LEAVE.
	AfterLeaveHandler func(ID uint32)
)

// an Handshaker impements the server-side part of the handshaking protocol.
type Handshaker interface {

	// Join should process the JOIN message of the Handshaking protocol, checks
	// that the conditions are met in order to accept the emitter for the JOIN
	// message. If that is the case, true is returned. In both cases, it should
	// take care of the required steps in order to follow the defined
	// handshaking protocol (i.e send/broadcast messages, etc.).
	Join(join messages.JoinMsg, c *network.Conn) bool

	// Leave executes the LEAVE step of the Handshaking protocol on the client
	// associtated to the connection c.
	Leave(reason string, c *network.Conn)

	// AfterJoinHandler returns the registered 'after join' handler, if any.
	AfterJoinHandler() AfterJoinHandler

	// SetAfterJoinHandler registers the 'after join' handler.
	SetAfterJoinHandler(AfterJoinHandler)

	// AfterLeaveHandler returns the registered 'after leave' handler, if any.
	AfterLeaveHandler() AfterLeaveHandler

	// SetAfterLeaveHandler registers the 'after leave' handler.
	SetAfterLeaveHandler(AfterLeaveHandler)
}

/*
 * registerTelnetCommands sets up the server-related command handlers
 */
func registerTelnetCommands(tns *TelnetServer, registry *ClientRegistry) {
	// 'kick' command
	kick := cli.Command{
		Name:  "kick",
		Usage: "politely ask a client to leave, then kick him",
		Flags: []cli.Flag{
			cli.IntFlag{Name: "id", Usage: "client id"},
		},
		Action: func(c *cli.Context) error {
			clientId := uint32(c.Int("id"))
			if connection, ok := registry.clients[clientId]; ok {
				registry.Leave("telnet just kicked your ass out", connection)
				io.WriteString(c.App.Writer,
					fmt.Sprintf("client %v has been kicked out\n", clientId))
			} else {
				io.WriteString(c.App.Writer, fmt.Sprintf("invalid client id\n"))
			}
			return nil
		},
	}
	tns.RegisterCommand(&kick)

	// 'clients' command
	clients := cli.Command{
		Name:  "clients",
		Usage: "shows the list of connected clients",
		Action: func(c *cli.Context) error {
			io.WriteString(c.App.Writer, fmt.Sprintf("connected clients:\n"))
			registry.ForEach(func(client ClientData) bool {
				io.WriteString(c.App.Writer, fmt.Sprintf(" * %v - %v\n", client.Name, client.Id))
				return true
			})
			return nil
		},
	}
	tns.RegisterCommand(&clients)
}
