/*
 * Surviveler entity package
 * types
 */
 package entity

/*
 * This interface represents an element that updates itself
 */
type Updater interface {
	Update(dt float32)
}

type Player struct {
	XPos, YPos float32
}

func (p *Player) Update(dt float32) {
	p.XPos = 10
	p.YPos = 15
}
