package game

import (
	"server/events"
	"server/math"
	"sync"
)

type EntityFilter func(e Entity) bool

type GameState interface {
	World() *World
	Entity(id uint32) Entity
	NearestEntity(pos math.Vec2, f EntityFilter) (Entity, float32)
	AddEntity(ent Entity)
	RemoveEntity(id uint32)
	GameTime() int16
}

type Game interface {
	Start()
	State() GameState
	QuitChan() chan struct{}
	PostEvent(*events.Event)
	Pathfinder() *Pathfinder
	WaitGroup() *sync.WaitGroup
}
