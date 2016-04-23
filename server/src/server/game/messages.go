package game

import ()

// Types of messages sent by the client
const (
	UserMove MsgType = 1 + iota
	UserAction
)

// Examples Messages
type UserMoveMsg struct {
	IncomingMsg
}
type UserActionMsg struct {
	IncomingMsg
}
