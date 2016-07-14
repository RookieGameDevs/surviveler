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
	Tstamp    int64
	Time      int16
	Entities  map[uint32]interface{}
	Buildings map[uint32]interface{}
	Objects   map[uint32]interface{}
}

/*
 * player initiated character movement. Client -> server message
 */
type MoveMsg struct {
	Xpos float32
	Ypos float32
}

/*
 * player initiated a building action. Client -> server message
 */
type BuildMsg struct {
	Type uint8
	Xpos float32
	Ypos float32
}

/*
 * player initiated a repair action. Client -> server message
 */
type RepairMsg struct {
	Id uint32 // id of the building to repair
}

/*
 * player initiated an attack action. Client -> server message
 */
type AttackMsg struct {
	Id uint32 // id of the entity to attack
}

/*
 * This message is sent only by clients right after a connection is
 * established.
 */
type JoinMsg struct {
	Name string
	Type uint8
}

/*
 * Message broadcasted to all clients by the server when a successful join was
 * accomplished.
 */
type JoinedMsg struct {
	Id   uint32
	Name string
	Type uint8
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
