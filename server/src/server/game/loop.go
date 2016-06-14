/*
 * Surviveler game package
 * game loop
 */

package game

import (
	msg "server/game/messages"
	"time"

	log "github.com/Sirupsen/logrus"
)

/*
 * loop is the main game loop, it fetches messages from a channel, processes
 * them immediately. After performing some initialization, it waits forever,
 * waiting for a wake-up call coming from any one of those events:
 * - external loop close request -> exits immediately
 * - arrival of a message -> process it
 * - logic tick -> perform logic update
 * - gamestate tick -> pack and broadcast the current game state
 * - telnet request -> perform a game state related telnet request
 */
func (g *Game) loop() error {
	// will tick when it's time to send the gamestate to the clients
	sendTickChan := time.NewTicker(
		time.Millisecond * time.Duration(g.cfg.SendTickPeriod)).C

	// will tick when it's time to update the game
	tickChan := time.NewTicker(
		time.Millisecond * time.Duration(g.cfg.LogicTickPeriod)).C

	// will tick when a minute in game time elapses
	timeChan := time.NewTicker(
		time.Minute * 1 / time.Duration(g.cfg.TimeFactor)).C

	// encapsulate the game state here, as it should not be
	// accessed nor modified from outside the game loop
	gs := newGameState(g)
	var err error
	if err = gs.init(g.assets); err != nil {
		return err
	}
	g.movementPlanner.setGameState(gs)

	msgmgr := new(msg.MessageManager)
	msgmgr.Listen(msg.MoveId, msg.MsgHandlerFunc(g.movementPlanner.onMovePlayer))
	msgmgr.Listen(msg.JoinedId, msg.MsgHandlerFunc(gs.onPlayerJoined))
	msgmgr.Listen(msg.LeaveId, msg.MsgHandlerFunc(gs.onPlayerLeft))
	msgmgr.Listen(msg.MovementRequestResultId, msg.MsgHandlerFunc(gs.onMovementRequestResult))

	var last_time, cur_time time.Time
	last_time = time.Now()
	log.Info("Starting game loop")
	g.wg.Add(1)

	go func() {
		defer func() {
			g.wg.Done()
			log.Info("Stopping game loop")
		}()

		for {
			select {

			case <-g.gameQuit:
				return

			case msg := <-g.msgChan:
				// dispatch msg to listeners
				if err := msgmgr.Dispatch(msg.Message, msg.ClientId); err != nil {
					// a listener can return an error, we log it but it should not
					// perturb the rest of the game
					log.WithField("err", err).Error("Dispatch returned an error")
				}

			case <-sendTickChan:
				// pack the gamestate into a message
				if gsMsg := gs.pack(); gsMsg != nil {
					// wrap the GameStateMsg into a generic Message
					if msg := msg.NewMessage(msg.GameStateId, *gsMsg); msg != nil {
						g.server.Broadcast(msg)
					}
				}

			case <-tickChan:
				// compute delta time
				cur_time = time.Now()
				dt := cur_time.Sub(last_time)

				// update AI
				gs.director.Update(cur_time)

				// update entities
				for _, ent := range gs.players {
					ent.Update(dt)
				}

				// update zombies
				for _, zom := range gs.zombies {
					zom.Update(dt)
				}
				last_time = cur_time

			case <-timeChan:
				// increment game time by 1 minute
				gs.gameTime++

				// clamp the game time to 24h
				if gs.gameTime >= 1440 {
					gs.gameTime -= 1440
				}

			case tnr := <-g.telnetReq:
				// received a telnet request
				g.telnetDone <- g.telnetHandler(tnr, gs)

			default:
				// let the rest of the world spin
				time.Sleep(1 * time.Millisecond)
			}
		}
	}()
	return nil
}
