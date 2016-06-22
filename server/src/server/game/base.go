package game

import (
	"server/game/messages"
	"server/game/resource"
	"server/math"
	"sync"
)

type EntityFilter func(e Entity) bool

type GameState interface {
	GetWorld() *World
	GetEntity(id uint32) Entity
	GetNearestEntity(pos math.Vec2, f EntityFilter) (Entity, float32)
	AddEntity(ent Entity) uint32
	GetMapData() *resource.MapData
	GetGameTime() int16
}

type Game interface {
	Start()
	GetState() GameState
	GetQuitChan() chan struct{}
	GetMessageChan() chan messages.ClientMessage
	GetPathfinder() *Pathfinder
	GetWaitGroup() *sync.WaitGroup
}
