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
	PlayerBuild
	PlayerRepair
	PlayerAttack
	PathReady
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

type PlayerBuildEvent struct {
	Id   uint32
	Type uint8
	Xpos float32
	Ypos float32
}

type PlayerRepairEvent struct {
	Id         uint32
	BuildingId uint32
}

type PlayerAttackEvent struct {
	Id       uint32
	EntityId uint32
}

type PathReadyEvent struct {
	Id   uint32
	Path math.Path // the path found
}
