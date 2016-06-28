/*
 * Surviver protocol package
 * server implementation: actions
 */
package protocol

import (
	log "github.com/Sirupsen/logrus"
	"server/game/events"
	"server/game/messages"
	"server/network"
)

/*
 * handleMove processes a MoveMsg and fires a PlayerMove event
 */
func (self *Server) handleMove(c *network.Conn, msg *messages.Message) error {
	// decode payload into a move message
	move := self.factory.DecodePayload(messages.MoveId, msg.Payload).(messages.MoveMsg)
	log.WithField("msg", move).Info("Move message")

	clientData := c.GetUserData().(ClientData)

	evt := events.NewEvent(events.PlayerMove, events.PlayerMoveEvent{
		Id:   clientData.Id,
		Xpos: move.Xpos,
		Ypos: move.Ypos,
	})

	self.eventChan <- evt
	return nil
}
