/*
 * Surviveler game package
 * movement planner
 */
package game

import (
	"fmt"
	"server/game/events"
	msg "server/game/messages"
	"server/math"
	"time"

	log "github.com/Sirupsen/logrus"
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
	ringBufIn    chan *MovementRequest // lock-free ring buffer entry point
	ringBufOut   chan *MovementRequest // lock free ring buffer exit point (buffered channel)
	lastRequests map[uint32]time.Time  // record the last movement request, by entity id
	game         Game
}

/*
 * NewMovementPlanner initializes and return a MovementPlanner.
 *
 * There should be one and only one MovementPlanner instance in the game.
 * The MovementPlanner accepts a filled MovementRequest, places it in a
 * ring buffer. Pathfinding is then performed on the Movement Request, if the
 * request makes it up to this point.
 */
func NewMovementPlanner(game Game) *MovementPlanner {
	return &MovementPlanner{
		ringBufIn:    make(chan *MovementRequest),
		ringBufOut:   make(chan *MovementRequest, 10),
		lastRequests: make(map[uint32]time.Time),
		game:         game,
	}
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

	mp.game.GetWaitGroup().Add(1)
	// start the ring buffer goroutine
	go func() {
		defer func() {
			mp.game.GetWaitGroup().Done()
			close(mp.ringBufIn)
			close(mp.ringBufOut)
		}()
		for {

			select {

			case <-mp.game.GetQuitChan():
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
	mp.game.GetWaitGroup().Add(1)
	go func() {
		defer func() {
			log.Info("Stopping movement planner")
			mp.game.GetWaitGroup().Done()
		}()

		for {
			select {

			case <-mp.game.GetQuitChan():
				return

			case mvtReq := <-mp.ringBufOut:
				// read from the ring buffer
				if mvtReq == nil {
					return
				}
				log.WithField("req", mvtReq).Info("Processing an movement request")

				// compute pathfinding
				if path, _, found := mp.game.GetPathfinder().FindPath(mvtReq.Org, mvtReq.Dst); found {
					if len(path) > 1 {
						log.WithFields(log.Fields{"path": path, "req": mvtReq}).Debug("Pathfinder found a path")

						// fill and send a MovementRequestResultMsg to the game loop
						evt := events.NewEvent(
							events.PathCalculated,
							events.PathCalculatedEvent{
								Id:   mvtReq.EntityId,
								Path: path,
							})
						mp.game.GetEventChan() <- evt
					}
				} else {
					log.WithField("req", mvtReq).Warn("Pathfinder failed to find path")
				}
			}
		}
	}()
}

/*
 * OnMovePlayer handles the reception of a MoveMsg
 */
func (mp *MovementPlanner) OnMovePlayer(imsg interface{}, clientId uint32) error {
	move := imsg.(msg.MoveMsg)
	log.WithFields(log.Fields{"clientId": clientId, "msg": move}).Info("MovementPlanner.OnMovePlayer")

	if player := mp.game.GetState().GetEntity(clientId); player != nil {
		// fills a MovementRequest
		mvtReq := MovementRequest{}
		mvtReq.Org = player.GetPosition()
		mvtReq.Dst = math.FromFloat32(move.Xpos, move.Ypos)
		mvtReq.EntityId = clientId
		if mp.game.GetState().GetWorld().PointInBounds(mvtReq.Dst) {
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
