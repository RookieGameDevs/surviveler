/*
 * Surviveler protocol package
 * server implementation: handshake
 */
package protocol

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"github.com/urfave/cli"
	"io"
	"server/game/events"
	"server/game/messages"
	"server/network"
	"time"
)

/*
 * handlePing processes a PingMsg and immediately replies with a PongMsg
 */
func (srv *Server) handlePing(c *network.Conn, msg *messages.Message) error {
	// decode payload into a ping message
	ping := srv.factory.DecodePayload(messages.PingId, msg.Payload).(messages.PingMsg)
	log.WithField("msg", ping).Info("It's a Ping!")

	// reply pong
	pong := messages.NewMessage(messages.PongId,
		messages.PongMsg{
			Id:     ping.Id,
			Tstamp: time.Now().UnixNano() / int64(time.Millisecond),
		})
	if err := c.AsyncSendPacket(pong, time.Second); err != nil {
		return err
	}
	log.WithField("msg", pong).Info("Sent a Pong!")
	return nil
}

/*
 * handleJoin processes a JoinMsg, checking some conditions before eventually
 * accepting the client join request (or not). Inform other players and game
 * loop if the player is accepted.
 */
func (srv *Server) handleJoin(c *network.Conn, msg *messages.Message) error {
	// decode payload into a join message
	join := srv.factory.DecodePayload(messages.JoinId, msg.Payload).(messages.JoinMsg)
	log.WithFields(log.Fields{"name": join.Name, "type": join.Type}).Info("A client would like to join")

	clientData := c.GetUserData().(ClientData)

	// check if STAY conditions are met
	var reason string
	accepted := false

	switch {
	case clientData.Joined:
		reason = "Joined already received"
	case len(join.Name) < 3:
		reason = "Name is too short!"
	default:
		nameTaken := false
		stay := messages.StayMsg{
			Id:      clientData.Id,
			Players: make(map[uint32]string),
		}

		// compute the list of joined players in a closure
		srv.clients.ForEach(func(cd ClientData) bool {
			nameTaken = cd.Name == join.Name
			stay.Players[cd.Id] = cd.Name
			// stop iteration if name is taken
			return !nameTaken
		})
		if nameTaken {
			reason = "Name is already taken!"
			break
		}

		// send STAY to client
		log.WithField("id", clientData.Id).Info("Join conditions accepted, client can stay")
		err := c.AsyncSendPacket(messages.NewMessage(messages.StayId, stay), time.Second)
		if err != nil {
			return err
		}

		// broadcast JOINED
		joined := messages.NewMessage(messages.JoinedId, messages.JoinedMsg{
			Id:   clientData.Id,
			Name: join.Name,
			Type: join.Type,
		})
		log.WithField("joined", joined).Info("Tell to the world this client has joined")
		srv.Broadcast(joined)

		// informs the game loop that we have a new player
		evt := events.NewEvent(events.PlayerJoin, events.PlayerJoinEvent{
			Id:   clientData.Id,
			Type: join.Type,
		})
		srv.evtCb(evt)

		// consider the client as accepted
		clientData.Joined = true
		clientData.Name = join.Name
		c.SetUserData(clientData)
		accepted = true
	}

	if !accepted {
		sendLeave(c, reason)
	}
	return nil
}

/*
 * sendLeave sends a LEAVE message to the client associated to given connection
 */
func sendLeave(c *network.Conn, reason string) error {
	clientData := c.GetUserData().(ClientData)

	// send LEAVE to client
	leave := messages.NewMessage(messages.LeaveId, messages.LeaveMsg{
		Id:     uint32(clientData.Id),
		Reason: reason,
	})
	if err := c.AsyncSendPacket(leave, 5*time.Millisecond); err != nil {
		return err
	}
	log.WithField("leave", leave).Info("Client is kindly asked to leave")

	// closes the connection, registry cleanup will be performed in OnClose
	if !c.IsClosed() {
		c.Close()
	}
	return nil
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
				if err := sendLeave(connection, "telnet just kicked your ass out"); err != nil {
					io.WriteString(c.App.Writer,
						fmt.Sprintf("couldn't kick client %v\n", err))
				} else {
					io.WriteString(c.App.Writer,
						fmt.Sprintf("client %v has been kicked out\n", clientId))
				}
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
