package game

/*
 * Client - Server messages
 */
const (
	PingId MsgType = 0 + iota
	PongId
	PositionId
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
 * TEMP: entity position message in 2D space
 */
type PositionMsg struct{ Xpos, Ypos float32 }

/*
 * Indicates a new player is joining current session
 */
type NewPlayerMsg struct {
	Name string
}
