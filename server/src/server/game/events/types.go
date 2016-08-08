/*
 * Surviveler events package
 * event types
 */
package events

import (
	"server/math"
)

type Type uint16

const (
	PlayerJoinId = iota
	PlayerLeaveId
	PlayerMoveId
	PlayerBuildId
	PlayerRepairId
	PlayerAttackId
	PlayerOperateId
	PlayerDeathId
	ZombieDeathId
	BuildingDestroyId
	PathReadyId
)

type PlayerJoin struct {
	Id   uint32
	Type uint8
}

type PlayerLeave struct {
	Id uint32
}

type PlayerMove struct {
	Id   uint32
	Xpos float32
	Ypos float32
}

type PlayerBuild struct {
	Id   uint32
	Type uint8
	Xpos float32
	Ypos float32
}

type PlayerRepair struct {
	Id         uint32
	BuildingId uint32
}

type PlayerAttack struct {
	Id       uint32
	EntityId uint32
}

type PlayerOperate struct {
	Id       uint32
	EntityId uint32
}

type PlayerDeath struct {
	Id uint32
}

type ZombieDeath struct {
	Id uint32
}

type BuildingDestroy struct {
	Id uint32
}

type PathReady struct {
	Id   uint32
	Path math.Path // the path found
}
