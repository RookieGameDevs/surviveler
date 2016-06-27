/*
 * Surviveler events package
 * event types
 */
package events

import (
	"server/math"
)

type EventType uint16

const (
	PlayerJoin = iota
	PlayerLeave
	PlayerMove
	PathCalculated
)

type PlayerJoinEvent struct {
	Id   uint32
	Type uint8
}

type PlayerLeaveEvent struct {
	Id uint32
}

type PlayerMoveEvent struct {
	Id   uint32
	Xpos float32
	Ypos float32
}

type PathCalculatedEvent struct {
	Id   uint32
	Path math.Path // the path found
}
