/*
 * Surviveler game package
 * movement planner
 */
package game

import (
	"server/game/events"
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
							events.PathReady,
							events.PathReadyEvent{
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
 * OnMovePlayer handles the PlayerMove event
 */
func (mp *MovementPlanner) OnMovePlayer(event *events.Event) {
	playerMoveEvent := event.Payload.(events.PlayerMoveEvent)
	// new movement action issued by a player
	log.WithFields(log.Fields{"clientId": playerMoveEvent.Id, "msg": playerMoveEvent}).Info("MovementPlanner.OnMovePlayer")

	if player := mp.game.GetState().GetEntity(playerMoveEvent.Id); player != nil {
		// fills a MovementRequest
		mvtReq := MovementRequest{}
		mvtReq.Org = player.GetPosition()
		mvtReq.Dst = math.FromFloat32(playerMoveEvent.Xpos, playerMoveEvent.Ypos)
		mvtReq.EntityId = playerMoveEvent.Id
		if mp.game.GetState().GetWorld().PointInBounds(mvtReq.Dst) {
			// places it into the MovementPlanner
			mp.PlanMovement(&mvtReq)
		} else {
			// do not forward a request with out-of-bounds destination
			log.WithField("dst", mvtReq.Dst).Warn("Out of bounds destination in MoveMsg")
		}
	} else {
		log.WithField("id", playerMoveEvent.Id).Warn("Client Id not found")
	}
}
