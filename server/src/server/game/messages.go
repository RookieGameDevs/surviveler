package game

/*
 * Client - Server messages
 */
const (
	PingId MsgType = 0 + iota
	PongId
	GameStateId
)

/*
 * Server only messages
 */
const (
	NewPlayerId = 1024 + iota
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
 * Indicates a new player is joining current session
 */
type NewPlayerMsg struct {
	Name string
}

type GameStateMsg struct {
	Tstamp int64
	Xpos   float32
	Ypos   float32
	Action ActionMsg
}

type ActionMsg struct {
	ActionType   uint16
	TargetTstamp int64
	Xpos         float32
	Ypos         float32
}
