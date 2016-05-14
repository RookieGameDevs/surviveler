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
	GameStateId
	MoveId
)

/*
 * Server only messages
 * TODO: those will be replaced once the handshake protocol will be implemented
 */
const (
	AddPlayerId = 1024 + iota
	DelPlayerId
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
	Entities map[uint16]interface{}
}

/*
 * player initiated character movement. Client -> server message
 */
type MoveMsg struct {
	Xpos float32
	Ypos float32
}

/*
 * Indicates a new player joined the game
 */
type AddPlayerMsg struct {
	Name string
}

/*
 * Indicates that a player may be removed
 */
type DelPlayerMsg struct{}
