/*
	Message interfaces
*/
package core

import (
	"net"
)

// Message is the interface that wraps the Serialize method.
type Message interface {

	// Serialize transforms the message into a buffer of bytes.
	Serialize() []byte
}

// MessageReader is the interface that wraps the ReadMessage method.
type MessageReader interface {

	// ReadMessage reads a message from a TCP connection, or returns an error
	// in case of failure.
	ReadMessage(conn *net.TCPConn) (Message, error)
}
