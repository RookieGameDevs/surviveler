/*
 * Surviveler messages package
 * message types & identifiers
 */
package messages

/*
 * Client - Server messages
 */
const (
	PingId uint16 = 0 + iota
	PongId
	JoinId
	JoinedId
	StayId
	LeaveId
	GameStateId
	MoveId
	BuildId
	RepairId
	AttackId
	OperateId
)

/*
 * Client->server time synchronization message
 */
type Ping struct {
	Id     uint32
	Tstamp int64
}

/*
 * Server->client time synchronization message
 */
type Pong Ping

/*
 * Server->client game state
 */
type GameState struct {
	Tstamp    int64
	Time      int16
	Entities  map[uint32]interface{}
	Buildings map[uint32]interface{}
	Objects   map[uint32]interface{}
}

/*
 * player initiated character movement. Client -> server message
 */
type Move struct {
	Xpos float32
	Ypos float32
}

/*
 * player initiated a building action. Client -> server message
 */
type Build struct {
	Type uint8
	Xpos float32
	Ypos float32
}

/*
 * player initiated a repair action. Client -> server message
 */
type Repair struct {
	Id uint32 // id of the building to repair
}

/*
 * player initiated an attack action. Client -> server message
 */
type Attack struct {
	Id uint32 // id of the entity to attack
}

/*
 * player initiated an operate action. Client -> server message
 */
type Operate struct {
	Id uint32 // id of the entity to operate
}

/*
 * This message is sent only by clients right after a connection is
 * established.
 */
type Join struct {
	Name string
	Type uint8
}

/*
 * Message broadcasted to all clients by the server when a successful join was
 * accomplished.
 */
type Joined struct {
	Id   uint32
	Name string
	Type uint8
}

/*
 * Response to a `JOIN` message, sent only by server to the client which
 * requested to join.
 */
type Stay struct {
	Id      uint32
	Players map[uint32]string
}

/*
 * Response to a bad `JOIN` request *OR* broadcast message sent at any point
 * during play.
 */
type Leave struct {
	Id     uint32
	Reason string
}
