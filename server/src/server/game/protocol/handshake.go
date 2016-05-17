/*
 * Surviveler protocol package
 * server implementation: handshake
 */
package protocol

import (
	log "github.com/Sirupsen/logrus"
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
	log.WithField("name", join.Name).Info("A client would like to join")

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
			// stop iteratio if name is taken
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
		})
		log.WithField("joined", joined).Info("Tell to the world this client has joined")
		srv.Broadcast(joined)

		// informs the game loop that we have a new player
		srv.msgcb(messages.NewMessage(messages.JoinedId, joined), clientData.Id)

		// consider the client as accepted
		clientData.Joined = true
		clientData.Name = join.Name
		c.SetUserData(clientData)
		accepted = true
	}

	if !accepted {
		// send LEAVE to client
		leave := messages.NewMessage(messages.LeaveId, messages.LeaveMsg{
			Id:     uint32(clientData.Id),
			Reason: reason,
		})
		if err := c.AsyncSendPacket(leave, time.Second); err != nil {
			return err
		}
		log.WithFields(log.Fields{
			"id": clientData.Id, "reason": reason}).
			Info("Client not accepted, tell him to leave")
		// closes the connection, registry cleanup will be performed in OnClose
		c.Close()
	}
	return nil
}
