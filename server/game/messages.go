package game

import (
	"bitbucket.com/rookiegamedevs/surviveler/server/core"
)

// Types of messages sent by the client
const (
	UserMove core.MsgType = 1 + iota
	UserAction
)

// Examples Messages
type UserMoveMsg struct {
	core.IncomingMsg
}
type UserActionMsg struct {
	core.IncomingMsg
}
