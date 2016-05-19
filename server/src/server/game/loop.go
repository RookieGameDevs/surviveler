/*
 * Surviveler game package
 * game loop
 */

package game

import (
	log "github.com/Sirupsen/logrus"
	"server/game/messages"
	"time"
)

/*
 * loop is the main game loop, it fetches messages from a channel, processes
 * them immediately. After performing some initialization, it waits forever,
 * waiting a wake-up call from any one of those events:
 * - external loop close request -> exits immediately
 * - arrival of a message -> process it
 * - logic tick -> perform logic update
 * - gamestate tick: pack and broadcast the current game state
 */
func (g *Game) loop() {

	// will tick when it's time to send the gamestate to the clients
	sendTickChan := time.NewTicker(
		time.Millisecond * time.Duration(g.cfg.SendTickPeriod)).C

	// will tick when it's time to update the game
	tickChan := time.NewTicker(
		time.Millisecond * time.Duration(g.cfg.LogicTickPeriod)).C

	// encapsulate the game state here, as it should not be accessed nor modified
	// from outside the game loop
	gs := NewGameState()

	msgmgr := new(messages.MessageManager)
	msgmgr.Listen(messages.MoveId, messages.MsgHandlerFunc(gs.onMovePlayer))
	msgmgr.Listen(messages.JoinedId, messages.MsgHandlerFunc(gs.onPlayerJoined))
	msgmgr.Listen(messages.LeaveId, messages.MsgHandlerFunc(gs.onPlayerLeft))

	// loop local stop condition
	quit := false

	var last_time, cur_time time.Time
	last_time = time.Now()

	go func() {
		for !quit {
			select {

			case <-g.loopCloseChan:
				quit = true

			case msg := <-g.msgChan:
				// dispatch msg to listeners
				if err := msgmgr.Dispatch(msg.Message, msg.ClientId); err != nil {
					log.WithField("err", err).Error("Dispatch returned an error")
				}

			case <-sendTickChan:
				// pack the gamestate into a message
				if gsMsg := gs.pack(); gsMsg != nil {
					// wrap the GameStateMsg into a generic Message
					if msg := messages.NewMessage(messages.GameStateId, *gsMsg); msg != nil {
						g.server.Broadcast(msg)
					}
				}

			case <-tickChan:
				// compute delta time
				cur_time = time.Now()
				dt := cur_time.Sub(last_time)

				// tick game: update entities
				for _, ent := range gs.players {
					ent.Update(dt)
				}
				last_time = cur_time

			case tnm := <-g.telnetChan:
				// received an message from telnet
				g.telnetHandler(tnm, &gs)

			default:

				// let the rest of the world spin
				time.Sleep(1 * time.Millisecond)
			}
		}
		log.Info("Game just stopped ticking")
	}()
}
