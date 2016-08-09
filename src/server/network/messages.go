/*
 * Generic network package
 * interfaces
 */
package network

import (
	"net"
)

/*
 * Packet is the interface that wraps the Serialize method.
 */
type Packet interface {

	// Serialize transforms the packet into a buffer of bytes.
	Serialize() []byte
}

/*
 * PacketReader is the interface that wraps the ReadPacket method.
 */
type PacketReader interface {

	// ReadPacket reads a message from a TCP connection, or returns an error
	// in case of failure.
	ReadPacket(conn *net.TCPConn) (Packet, error)
}
