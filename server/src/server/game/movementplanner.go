/*
 * Surviveler game package
 * movement planner
 */
package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	msg "server/game/messages"
	"server/math"
	"sync"
	"time"
)

// min duration between 2 pathfinding request for the same player
const pathfinderMinPeriod = time.Duration(400) * time.Millisecond

// represent the server id for server only messages
const serverOnly uint32 = 1<<32 - 1

type MovementRequest struct {
	Org, Dst math.Vec2
	EntityId uint32
}

type MovementPlanner struct {
	ringBufIn    chan *MovementRequest  // lock-free ring buffer entry point
	ringBufOut   chan *MovementRequest  // lock free ring buffer exit point (buffered channel)
	msgChan      chan msg.ClientMessage // to send messages to the game loop
	gameQuit     chan struct{}          // used to signal game exit
	wg           *sync.WaitGroup        // synchronizaton at game exit
	lastRequests map[uint32]time.Time   // record the last movement request, by entity id
	gameState    *GameState
	pathfinder   *Pathfinder
	world        *World
}

/*
 * NewMovementPlanner initializes and return a MovementPlanner.
 *
 * There should be one and only one MovementPlanner instance in the game.
 * The MovementPlanner accepts a filled MovementRequest, places it in a
 * ring buffer. Pathfinding is then performed on the Movement Request, if the
 * request makes it up to this point.
 */
func NewMovementPlanner(game *Game) *MovementPlanner {
	mp := MovementPlanner{
		ringBufIn:    make(chan *MovementRequest),
		ringBufOut:   make(chan *MovementRequest, 10),
		msgChan:      game.msgChan,
		gameQuit:     game.gameQuit,
		wg:           &game.wg,
		lastRequests: make(map[uint32]time.Time),
	}
	return &mp
}

/*
 * setGameState provides external instance to the movement planner
 */
func (mp *MovementPlanner) setGameState(gs *GameState) {
	mp.gameState = gs
	mp.pathfinder = &(gs.Pathfinder)
	mp.world = gs.Pathfinder.World
}

/*
 * PlanMovement places a new movement request in the planner.
 *
 * The movement request will remove any previous movement request made for the
 * same entity.
 */
func (mp *MovementPlanner) PlanMovement(mvtReq *MovementRequest) {
	// check the time elapsed since last planned request
	doIt := true
	if last, ok := mp.lastRequests[mvtReq.EntityId]; ok {
		doIt = time.Since(last) > pathfinderMinPeriod
	}
	if doIt {
		// insert the movement request in the ringbuffer
		mp.ringBufIn <- mvtReq
		mp.lastRequests[mvtReq.EntityId] = time.Now()
		log.WithField("req", *mvtReq).Info("Movement Request added to the planner")
	} else {
		log.WithField("req", *mvtReq).Info("Movement Request discarded because it was too close to previous one")
	}
}

/*
 * Start runs the movement planner loop.
 *
 * This method returns immediately as the movement planner loop runs in its own
 * goroutine
 */
func (mp *MovementPlanner) Start() {
	log.Info("Starting movement planner")

	mp.wg.Add(1)
	// start the ring buffer goroutine
	go func() {
		defer func() {
			mp.wg.Done()
			close(mp.ringBufIn)
			close(mp.ringBufOut)
		}()
		for {

			select {

			case <-mp.gameQuit:
				return

			case req := <-mp.ringBufIn:

				// we have a request
				select {

				case mp.ringBufOut <- req:
					// it succeeded so nothing more to do

				default:
					// out channel is full so we discard the oldest one
					oldMvtReq := <-mp.ringBufOut
					log.WithField("req", oldMvtReq).Warning("Discarded an old movement request")
					mp.ringBufOut <- req
				}
			}
		}
	}()

	// start the movent planner goroutine
	mp.wg.Add(1)
	go func() {
		defer func() {
			log.Info("Stopping movement planner")
			mp.wg.Done()
		}()

		for {
			select {

			case <-mp.gameQuit:
				return

			case mvtReq := <-mp.ringBufOut:
				// read from the ring buffer
				if mvtReq == nil {
					return
				}
				log.WithField("req", mvtReq).Info("Processing an movement request")

				// compute pathfinding
				if path, _, found := mp.pathfinder.FindPlayerPath(mvtReq.Org, mvtReq.Dst); found {
					if len(path) > 1 {
						log.WithFields(log.Fields{"path": path, "req": mvtReq}).Debug("Pathfinder found a path")

						// fill and send a MovementRequestResultMsg to the game loop
						mp.msgChan <- msg.ClientMessage{
							ClientId: serverOnly,
							Message: msg.NewMessage(
								msg.MovementRequestResultId,
								msg.MovementRequestResultMsg{
									EntityId: mvtReq.EntityId,
									Path:     path,
								}),
						}
					}
				} else {
					log.WithField("req", mvtReq).Warn("Pathfinder failed to find path")
				}
			}
		}
	}()
}

/*
 * onMovePlayer handles the reception of a MoveMsg
 */
func (mp *MovementPlanner) onMovePlayer(imsg interface{}, clientId uint32) error {
	move := imsg.(msg.MoveMsg)
	log.WithFields(log.Fields{"clientId": clientId, "msg": move}).Info("MovementPlanner.onMovePlayer")

	if player, ok := mp.gameState.players[clientId]; ok {
		// fills a MovementRequest
		mvtReq := MovementRequest{}
		mvtReq.Org = player.Pos
		mvtReq.Dst = math.Vec2{move.Xpos, move.Ypos}
		mvtReq.EntityId = clientId
		if mp.world.PointInBound(mvtReq.Dst) {
			// places it into the MovementPlanner
			mp.PlanMovement(&mvtReq)
		} else {
			// do not forward a request with out-of-bounds destination
			log.WithField("dst", mvtReq.Dst).Warn("Out of bounds destination in MoveMsg")
			return fmt.Errorf("Out of bounds destination: %v", mvtReq.Dst)
		}
	} else {
		return fmt.Errorf("Client Id not found: %v", clientId)
	}
	return nil
}
