/*
 * Surviveler game package
 * movement planner
 */
package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"server/game/messages"
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
	mvtReqInChan  chan *MovementRequest       // lock-free ring buffer entry point
	mvtReqOutChan chan *MovementRequest       // lock free ring buffer exit point (buffered channel)
	msgChan       chan messages.ClientMessage // to send messages to the game loop
	gameQuitChan  chan struct{}               // used to signal game exit
	waitGroup     *sync.WaitGroup             // synchronizaton at game exit
	lastRequests  map[uint32]time.Time        // record the last movement request, by entity id
	gameState     *GameState
	pathfinder    *Pathfinder
	world         *World
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
		mvtReqInChan:  make(chan *MovementRequest),
		mvtReqOutChan: make(chan *MovementRequest, 10),
		msgChan:       game.msgChan,
		gameQuitChan:  game.gameQuitChan,
		waitGroup:     &game.waitGroup,
		lastRequests:  make(map[uint32]time.Time),
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
		mp.mvtReqInChan <- mvtReq
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
	log.Info("Starting the movement planner")

	// start the ring buffer goroutine
	go func() {
		mp.waitGroup.Add(1)
		quit := false

		for !quit {
			select {

			case <-mp.gameQuitChan:
				quit = true

			case req := <-mp.mvtReqInChan:
				// we have a request
				select {
				case mp.mvtReqOutChan <- req:
					// it succeeded so nothing more to do

				default:
					// out channel is full so we discard the oldest one
					oldMvtReq := <-mp.mvtReqOutChan
					log.WithField("req", oldMvtReq).Warning("Discarded an old movement request")
					mp.mvtReqOutChan <- req
				}
			}
		}
		mp.waitGroup.Done()
		close(mp.mvtReqInChan)
		close(mp.mvtReqOutChan)
	}()

	// start the movent planner goroutine
	go func() {
		mp.waitGroup.Add(1)
		quit := false

		for !quit {
			select {

			case <-mp.gameQuitChan:
				quit = true

			case mvtReq := <-mp.mvtReqOutChan:
				// read from the ring buffer
				log.WithField("req", mvtReq).Info("Processing an movement request")

				// compute pathfinding
				if path, _, found := mp.pathfinder.FindPlayerPath(mvtReq.Org, mvtReq.Dst); found {
					if len(path) > 1 {
						log.WithFields(log.Fields{"path": path, "req": mvtReq}).Debug("Pathfinder found a path")

						// fill and send a MovementRequestResultMsg to the game loop
						mp.msgChan <- messages.ClientMessage{
							ClientId: serverOnly,
							Message: messages.NewMessage(
								messages.MovementRequestResultId,
								messages.MovementRequestResultMsg{
									EntityId: mvtReq.EntityId,
									Path:     path,
								}),
						}
					} else {
						//log.WithFields(log.Fields{"path": path, "req": mvtReq}).
						//Panic("Path must have at least 1 segment!")
					}
				} else {
					log.WithField("req", mvtReq).Warn("Pathfinder failed to find path")
				}
			}
		}
		mp.waitGroup.Done()
		log.Debug("Movement planner main goroutine has ended")
	}()
}

/*
 * onMovePlayer fills a MovementRequest and sends it to the MovementPlanner
 */
func (mp *MovementPlanner) onMovePlayer(msg interface{}, clientId uint32) error {
	move := msg.(messages.MoveMsg)
	log.WithFields(log.Fields{"clientId": clientId, "msg": move}).Info("MovementPlanner.onMovePlayer")

	if player, ok := mp.gameState.players[clientId]; ok {
		mvtReq := MovementRequest{}
		mvtReq.Org = player.Pos
		mvtReq.Dst = math.Vec2{move.Xpos, move.Ypos}
		mvtReq.EntityId = clientId
		if mp.world.PointInBound(mvtReq.Dst) {
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
