/*
 * Surviveler messages package
 * message types & identifiers
 */
package messages

import (
	"server/math"
)

/*
 * Client - Server messages
 */
const (
	PingId uint16 = 0 + iota
	PongId
	GameStateId
	MoveId
	JoinId
	JoinedId
	StayId
	LeaveId
)

/*
 * Client->server time synchronization message
 */
type PingMsg struct {
	Id     uint32
	Tstamp int64
}

/*
 * Server->client time synchronization message
 */
type PongMsg PingMsg

/*
 * Server->client game state
 */
type GameStateMsg struct {
	Tstamp   int64
	Time     int16
	Entities map[uint32]interface{}
}

/*
 * player initiated character movement. Client -> server message
 */
type MoveMsg struct {
	Xpos float32
	Ypos float32
}

/*
 * This message is sent only by clients right after a connection is
 * established.
 */
type JoinMsg struct {
	Name string
}

/*
 * Message broadcasted to all clients by the server when a successful join was
 * accomplished.
 */
type JoinedMsg struct {
	Id   uint32
	Name string
}

/*
 * Response to a `JOIN` message, sent only by server to the client which
 * requested to join.
 */
type StayMsg struct {
	Id      uint32
	Players map[uint32]string
}

/*
 * Response to a bad `JOIN` request *OR* broadcast message sent at any point
 * during play.
 */
type LeaveMsg struct {
	Id     uint32
	Reason string
}

/*
 * Server only messages
 */
const (
	MovementRequestResultId uint16 = 1024 + iota
)

/*
 * The result of a successfull movement request computation
 */
type MovementRequestResultMsg struct {
	EntityId uint32    // Id of the entity for which pathfinding was computed
	Path     math.Path // the path found
}
