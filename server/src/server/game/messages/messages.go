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
	Tstamp int64
	Xpos   float32
	Ypos   float32
	Action ActionMsg
}

/*
 * Sub-message of GameStateMsg.
 */
type ActionMsg struct {
	ActionType   uint16
	TargetTstamp int64
	Xpos         float32
	Ypos         float32
}

/*
 * player initiated character movement
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
