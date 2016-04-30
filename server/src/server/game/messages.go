package game

const (
	PingId MsgType = 0 + iota
	PongId
	PositionId
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
