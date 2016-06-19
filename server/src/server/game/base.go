package game

import (
	"server/game/messages"
	"server/game/resource"
	"sync"
)

type GameState interface {
	GetWorld() *World
	GetEntity(id uint32) Entity
	AddEntity(ent Entity) uint32
	GetMapData() *resource.MapData
}

type Game interface {
	Start()
	GetState() GameState
	GetQuitChan() chan struct{}
	GetMessageChan() chan messages.ClientMessage
	GetPathfinder() *Pathfinder
	GetWaitGroup() *sync.WaitGroup
}
