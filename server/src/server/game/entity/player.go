/*
 * Surviveler entity package
 * player
 */
package entity

import (
	"server/game/messages"
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
	mover.SetDestPos(math.Vec2{startX, startY})
	mover.SetSpeed(speed)

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

func (p *Player) GetAction() (messages.ActionType, interface{}) {
	if p.mover.HasReachedDestination() {
		return messages.IdleAction, messages.IdleActionData{}
	} else {
		dst := p.mover.GetDestPos()
		return messages.MoveAction, messages.MoveActionData{
			Speed: p.mover.GetSpeed(),
			Xpos:  dst[0],
			Ypos:  dst[1],
		}
	}
}

/*
 * EntityMover is a Mover implementation moving an element in straight line
 */
type EntityMover struct {
	pos     math.Vec2 // current position
	dst     math.Vec2 // final destination
	speed   float32   // speed
	reached bool
}

func (em *EntityMover) HasReachedDestination() bool {
	return em.reached
}

/*
 * SetPos defines the mover current position
 */
func (em *EntityMover) SetPos(pos math.Vec2) {
	em.pos = pos
	em.reached = false
}

/*
 * GetPos retrieves the mover current position
 */
func (em *EntityMover) GetPos() math.Vec2 {
	return em.pos
}

/*
 * SetPos defines the mover destination
 */
func (em *EntityMover) SetDestPos(dst math.Vec2) {
	em.dst = dst
	em.reached = false
}

/*
 * GetPos retrieves the mover destination
 */
func (em *EntityMover) GetDestPos() math.Vec2 {
	return em.dst
}

func (em *EntityMover) SetSpeed(speed float32) {
	em.speed = speed
}

func (em *EntityMover) GetSpeed() float32 {
	return em.speed
}

func (em *EntityMover) Update(dt time.Duration) {
	// arrived at destination?
	if em.pos.ApproxEqualThreshold(em.dst, 0.01) {
		// destination reached
		em.reached = true
	} else {
		// compute translation vector
		moveVec := em.dst.Sub(em.pos).Normalize()
		em.pos = em.pos.Add(moveVec.Mul(float32(em.speed * float32(dt.Seconds()))))
	}
}
