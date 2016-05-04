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
 * Indicates a new player joined the game
 */
type AddPlayerMsg struct {
	Name string
}

/*
 * Indicates that a player may be removed
 */
type DelPlayerMsg struct{}

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
