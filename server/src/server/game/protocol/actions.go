/*
 * Surviver protocol package
 * server implementation: actions
 */
package protocol

import (
	"server/game/events"
	"server/game/messages"
	"server/network"

	log "github.com/Sirupsen/logrus"
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

/*
 * handleRepair processes a RepairMsg and fires a PlayerRepair event
 */
func (self *Server) handleRepair(c *network.Conn, msg *messages.Message) error {
	// decode payload into a repair message
	repair := self.factory.DecodePayload(messages.RepairId, msg.Payload).(messages.RepairMsg)
	log.WithField("msg", repair).Info("Repair message")

	self.evtCb(
		events.NewEvent(events.PlayerRepair,
			events.PlayerRepairEvent{
				Id:         c.GetUserData().(ClientData).Id,
				BuildingId: repair.Id,
			}))
	return nil
}

/*
 * handleAttack processes a AttackMsg and fires a PlayerAttack event
 */
func (self *Server) handleAttack(c *network.Conn, msg *messages.Message) error {
	// decode payload into a attack message
	attack := self.factory.DecodePayload(messages.AttackId, msg.Payload).(messages.AttackMsg)
	log.WithField("msg", attack).Info("Attack message")

	self.evtCb(
		events.NewEvent(events.PlayerAttack,
			events.PlayerAttackEvent{
				Id:       c.GetUserData().(ClientData).Id,
				EntityId: attack.Id,
			}))
	return nil
}

/*
 * handleOperate processes a OperateMsg and fires a PlayerOperate event
 */
func (self *Server) handleOperate(c *network.Conn, msg *messages.Message) error {
	// decode payload into a operate message
	operate := self.factory.DecodePayload(messages.OperateId, msg.Payload).(messages.OperateMsg)
	log.WithField("msg", operate).Info("Operate message")

	self.evtCb(
		events.NewEvent(events.PlayerOperate,
			events.PlayerOperateEvent{
				Id:       c.GetUserData().(ClientData).Id,
				EntityId: operate.Id,
			}))
	return nil
}
