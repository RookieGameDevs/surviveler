/*
 * Surviveler game package
 * movement planner
 */
package game

import (
	log "github.com/Sirupsen/logrus"
	"server/math"
	"sync"
)

// one client action can be decomposed into 2 actions:
// -client clicks on coffee machine
// => go to coffee-machine + drink

// -client clicks on zombie
// => follow zombie + attack zombie

// We must have a component that manage this

const (
	Success uint = iota
	Failed  uint = iota
)

type MovementRequestResult struct {
	Result uint
	Path   []math.Vec2
	Reason string
}

type MovementRequestId uint

type MovementRequest struct {
	Id          MovementRequestId
	Destination math.Vec2
	EntityId    uint32
	Callback    func(MovementRequestResult)
}

type MovementPlanner struct {
	loopCloseChan chan struct{}
	waitGroup     *sync.WaitGroup
}

func NewMovementPlanner(loopCloseChan chan struct{}, waitGroup *sync.WaitGroup) *MovementPlanner {
	return &MovementPlanner{
		loopCloseChan: loopCloseChan,
		waitGroup:     waitGroup,
	}
}

/*
 * PlanMovement places a new movement request in the planner.
 *
 * The movement request will remove any previous movement request made for the
 * same entity.
 */
func (mp *MovementPlanner) PlanMovement(mr MovementRequest) MovementRequestId {

	// remove any pre-existing request for the same entity Id

	// insert the movement request in the planner

	// return the request Id
	return 0
}

/*
 * Start run the movement planner loop.
 *
 * This method returns immediately as the movement planner loop runs in its own
 * goroutine
 */
func (mp *MovementPlanner) Start() {

	log.Info("Starting the movement planner")

	go func() {
		mp.waitGroup.Add(1)
		defer func() {
			log.Info("Stopping movement planner")
			mp.waitGroup.Done()
		}()

		quit := false
		for !quit {
			select {
			case <-mp.loopCloseChan:
				quit = true
			}
		}
	}()
}
