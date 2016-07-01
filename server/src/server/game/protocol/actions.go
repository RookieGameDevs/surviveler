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

	self.evtCb(evt)
	return nil
}

/*
 * handleBuild processes a BuildMsg and fires a PlayerBuild event
 */
func (self *Server) handleBuild(c *network.Conn, msg *messages.Message) error {
	// decode payload into a move message
	build := self.factory.DecodePayload(messages.BuildId, msg.Payload).(messages.BuildMsg)
	log.WithField("msg", build).Info("Build message")

	clientData := c.GetUserData().(ClientData)

	evt := events.NewEvent(events.PlayerBuild, events.PlayerBuildEvent{
		Id:   clientData.Id,
		Type: build.Type,
		Xpos: build.Xpos,
		Ypos: build.Ypos,
	})

	self.evtCb(evt)
	return nil
}
