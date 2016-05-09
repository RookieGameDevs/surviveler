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

func (p *Player) SetDestination(dst math.Vec2) {

	// compute the destination timestamp
	p.mover.SetDestination(dst)
	p.ComputeDestinationTimestamp()
}

func (p *Player) GetDestination() math.Vec2 {
	return p.mover.GetDestination()
}

func (p *Player) GetDestinationTimestamp() int64 {
	return p.dstTstamp
}

func (p *Player) ComputeDestinationTimestamp() {

	org := p.mover.GetPos()
	dst := p.mover.GetDestination()
	speed := p.mover.GetSpeed()
	distance := dst.Sub(org).Len()
	duration := distance * speed
	dstTstamp := time.Now().Add(time.Duration(duration) * time.Second)

	// convert to int64
	p.dstTstamp = dstTstamp.UnixNano() / int64(time.Millisecond)
}

/*
 * EntityMover is a Mover implementation moving an element in straight line
 */
type EntityMover struct {
	pos   math.Vec2 // current position
	dst   math.Vec2 // destination
	speed float32   // speed

	// TODO: REMOVE THIS! this is for the test
	// record the original position to make the Entity goes back
	// and forth on screen
	Org math.Vec2
}

func (em *EntityMover) SetDestination(dst math.Vec2) {
	em.dst = dst
}

func (em *EntityMover) GetDestination() math.Vec2 {
	return em.dst
}

func (em *EntityMover) SetPos(pos math.Vec2) {
	em.pos = pos
}

func (em *EntityMover) GetPos() math.Vec2 {
	return em.pos
}

func (em *EntityMover) SetSpeed(speed float32) {
	em.speed = speed
}

func (em *EntityMover) GetSpeed() float32 {
	return em.speed
}

func (em *EntityMover) Update(dt time.Duration) {
	// compute displacement vector
	moveVec := em.dst.Sub(em.pos).Normalize()
	em.pos = em.pos.Add(moveVec.Mul(float32(em.speed * float32(dt.Seconds()))))

	// TODO: REMOVE THIS! this is for the test
	if em.pos.ApproxEqualThreshold(em.dst, 0.01) {
		// TEMP: swap dst and pos to make the entity goes back and forth
		tmp := em.dst
		em.dst = em.Org
		em.Org = tmp
	}
}
