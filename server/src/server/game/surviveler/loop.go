/*
 * Surviveler game package
 * game loop
 */

package surviveler

import (
	log "github.com/Sirupsen/logrus"
	"server/game/events"
	msg "server/game/messages"
	"time"
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
func (g *survivelerGame) loop() error {
	// will tick when it's time to send the gamestate to the clients
	sendTickChan := time.NewTicker(
		time.Millisecond * time.Duration(g.cfg.SendTickPeriod)).C

	// will tick when it's time to update the game
	tickChan := time.NewTicker(
		time.Millisecond * time.Duration(g.cfg.LogicTickPeriod)).C

	// will tick when a minute in game time elapses
	timeChan := time.NewTicker(
		time.Minute * 1 / time.Duration(g.cfg.TimeFactor)).C

	// message manager (and eventually listeners)
	msgmgr := new(msg.MessageManager)

	// event listeners
	g.eventManager.Subscribe(events.PlayerJoin, g.state.onPlayerJoin)
	g.eventManager.Subscribe(events.PlayerLeave, g.state.onPlayerLeave)
	g.eventManager.Subscribe(events.PlayerMove, g.state.OnPlayerMove)
	g.eventManager.Subscribe(events.PathReady, g.state.onPathReady)
	g.eventManager.Subscribe(events.PlayerBuild, g.state.onPlayerBuild)
	g.eventManager.Subscribe(events.PlayerRepair, g.state.onPlayerRepair)

	var lastTime, curTime time.Time
	lastTime = time.Now()
	log.Info("Starting game loop")
	g.wg.Add(1)

	go func() {
		defer func() {
			g.wg.Done()
			log.Info("Stopping game loop")
		}()

		for {
			select {

			case <-g.quitChan:
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
				if gsMsg := g.state.pack(); gsMsg != nil {
					// wrap the gameStateMsg into a generic Message
					if msg := msg.NewMessage(msg.GameStateId, *gsMsg); msg != nil {
						g.server.Broadcast(msg)
					}
				}

			case <-tickChan:
				// poll and process accumulated events
				g.eventManager.Process()

				// compute delta time
				curTime = time.Now()
				dt := curTime.Sub(lastTime)

				// update AI
				g.ai.Update(curTime)

				// update entities
				for _, ent := range g.state.entities {
					ent.Update(dt)
				}

				lastTime = curTime

			case <-timeChan:
				// increment game time by 1 minute
				g.state.gameTime++

				// clamp the game time to 24h
				if g.state.gameTime >= 1440 {
					g.state.gameTime -= 1440
				}

			case tnr := <-g.telnetReq:
				// received a telnet request
				g.telnetDone <- g.telnetHandler(tnr)

			default:
				// let the rest of the world spin
				time.Sleep(1 * time.Millisecond)
			}
		}
	}()
	return nil
}
