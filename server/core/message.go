/*
	Common Message definitions
*/
package core

import (
	"net"
)

type Message interface {
	Serialize() []byte
}

type MessageReader interface {
	ReadMessage(conn *net.TCPConn) (Message, error)
}
