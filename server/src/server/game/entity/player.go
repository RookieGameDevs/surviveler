/*
 * Surviveler entity package
 * player
 */
package entity

import (
	"server/math"
	"time"
)

/*
 * Player represents an entity that is controlled by a physical player. It
 * implements the Entity interface.
 */
type Player struct {
	mover     Mover
	dstTstamp int64 // timestamp at which the player will arrive
}

/*
 * NewPlayer creates a new player and set its initial position and speed
 */
func NewPlayer(startX, startY, speed float32) *Player {

	// config the mover
	mover := EntityMover{}
	mover.SetPos(math.Vec2{startX, startY})
	mover.SetSpeed(speed)

	// TODO: REMOVE THIS! this is for the test
	// this is for the test, set position so that the player can goes back and
	// forth on screen
	mover.Org = math.Vec2{startX, startY}
	return &Player{mover: &mover}
}

func (p *Player) Update(dt time.Duration) {
	p.mover.Update(dt)
}

func (p *Player) SetPos(pos math.Vec2) {
	p.mover.SetPos(pos)
}

func (p *Player) GetPos() math.Vec2 {
	return p.mover.GetPos()
}

func (p *Player) GetSnapshot() *ActionSnapshot {
	// for now an action snapshot is enough to represent the whole entity snapshot,
	// but that won't always be the case...
	return p.mover.GetSnapshot()
}

/*
 * EntityMover is a Mover implementation moving an element in straight line
 */
type EntityMover struct {
	pos     math.Vec2 // current position
	dst     math.Vec2 // final destination
	speed   float32   // speed
	reached bool

	// TODO: REMOVE THIS! this is for the test
	// record the original position to make the Entity goes back
	// and forth on screen
	Org math.Vec2
}

func (em *EntityMover) HasReachedDestination() bool {
	return em.reached
}

/*
 * SetPos defines the mover final destination
 */
func (em *EntityMover) SetPos(dst math.Vec2) {
	em.dst = dst
	em.reached = false
}

/*
 * GetPos retrieves the mover final destination
 */
func (em *EntityMover) GetPos() math.Vec2 {
	return em.dst
}

func (em *EntityMover) SetSpeed(speed float32) {
	em.speed = speed
}

func (em *EntityMover) Update(dt time.Duration) {
	// compute translation vector
	moveVec := em.dst.Sub(em.pos).Normalize()
	em.pos = em.pos.Add(moveVec.Mul(float32(em.speed * float32(dt.Seconds()))))

	// arrived at destination?
	if em.pos.ApproxEqualThreshold(em.dst, 0.01) {
		// TODO: REMOVE THIS! this is for the test
		//       swap dst and pos to make the entity goes back and forth
		tmp := em.dst
		em.dst = em.Org
		em.Org = tmp

		// destination reached
		//em.reached = true
	}
}

func (em *EntityMover) GetSnapshot() *ActionSnapshot {

	// compute timestamp at destination
	speed := em.speed
	distance := em.dst.Sub(em.pos).Len()
	duration := distance / speed
	dstTime := time.Now().Add(time.Duration(duration) * time.Second)
	dstTstamp := dstTime.UnixNano() / int64(time.Millisecond)

	return &ActionSnapshot{
		CurPos:     em.pos,
		DestPos:    em.dst,
		CurSpeed:   em.speed,
		DestTstamp: dstTstamp,
	}
}
