// TODO:
// THIS FILE COULD AND SHOULD BE GENERATED
package surviveler

import (
	"server/game/events"
	"server/game/messages"
	"server/game/protocol"
	"server/network"

	log "github.com/Sirupsen/logrus"
)

func (g *survivelerGame) registerMsgHandlers() {
	g.server.RegisterMsgHandler(messages.MoveId, g.handleMove)
	g.server.RegisterMsgHandler(messages.BuildId, g.handleBuild)
	g.server.RegisterMsgHandler(messages.RepairId, g.handleRepair)
	g.server.RegisterMsgHandler(messages.AttackId, g.handleAttack)
	g.server.RegisterMsgHandler(messages.OperateId, g.handleOperate)
}

/*
 * handleMove processes a MoveMsg and fires a PlayerMove event
 */
func (g *survivelerGame) handleMove(c *network.Conn, msg interface{}) error {
	move := msg.(messages.MoveMsg)
	log.WithField("msg", move).Info("Move message")

	g.eventManager.PostEvent(
		events.NewEvent(
			events.PlayerMove,
			events.PlayerMoveEvent{
				Id:   (c.GetUserData().(protocol.ClientData)).Id,
				Xpos: move.Xpos, Ypos: move.Ypos,
			}))
	return nil
}

/*
 * handleBuild processes a BuildMsg and fires a PlayerBuild event
 */
func (g *survivelerGame) handleBuild(c *network.Conn, msg interface{}) error {
	build := msg.(messages.BuildMsg)
	log.WithField("msg", build).Info("Build message")

	g.eventManager.PostEvent(
		events.NewEvent(events.PlayerBuild,
			events.PlayerBuildEvent{
				Id:   c.GetUserData().(protocol.ClientData).Id,
				Type: build.Type,
				Xpos: build.Xpos, Ypos: build.Ypos,
			}))
	return nil
}

/*
 * handleRepair processes a RepairMsg and fires a PlayerRepair event
 */
func (g *survivelerGame) handleRepair(c *network.Conn, msg interface{}) error {
	repair := msg.(messages.RepairMsg)
	log.WithField("msg", repair).Info("Repair message")

	g.eventManager.PostEvent(
		events.NewEvent(events.PlayerRepair,
			events.PlayerRepairEvent{
				Id:         c.GetUserData().(protocol.ClientData).Id,
				BuildingId: repair.Id,
			}))
	return nil
}

/*
 * handleAttack processes a AttackMsg and fires a PlayerAttack event
 */
func (g *survivelerGame) handleAttack(c *network.Conn, msg interface{}) error {
	attack := msg.(messages.AttackMsg)
	log.WithField("msg", attack).Info("Attack message")

	g.eventManager.PostEvent(
		events.NewEvent(events.PlayerAttack,
			events.PlayerAttackEvent{
				Id:       c.GetUserData().(protocol.ClientData).Id,
				EntityId: attack.Id,
			}))
	return nil
}

/*
 * handleOperate processes a OperateMsg and fires a PlayerOperate event
 */
func (g *survivelerGame) handleOperate(c *network.Conn, msg interface{}) error {
	operate := msg.(messages.OperateMsg)
	log.WithField("msg", operate).Info("Operate message")

	g.eventManager.PostEvent(
		events.NewEvent(events.PlayerOperate,
			events.PlayerOperateEvent{
				Id:       c.GetUserData().(protocol.ClientData).Id,
				EntityId: operate.Id,
			}))
	return nil
}
