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

	self.evtCb(
		events.NewEvent(
			events.PlayerMove,
			events.PlayerMoveEvent{
				Id:   (c.GetUserData().(ClientData)).Id,
				Xpos: move.Xpos, Ypos: move.Ypos,
			}))
	return nil
}

/*
 * handleBuild processes a BuildMsg and fires a PlayerBuild event
 */
func (self *Server) handleBuild(c *network.Conn, msg *messages.Message) error {
	// decode payload into a build message
	build := self.factory.DecodePayload(messages.BuildId, msg.Payload).(messages.BuildMsg)
	log.WithField("msg", build).Info("Build message")

	self.evtCb(
		events.NewEvent(events.PlayerBuild,
			events.PlayerBuildEvent{
				Id:   c.GetUserData().(ClientData).Id,
				Type: build.Type,
				Xpos: build.Xpos, Ypos: build.Ypos,
			}))
	return nil
}
