/*
 * Surviveler protocol package
 * message encoding & decoding
 */
package protocol

import (
	"encoding/binary"
	"fmt"
	"net"
	"server/messages"
	"server/network"
)

/*
 * value used to check the length of a client message before allocating
 * a buffer, in case the received size was wrong
 */
const MaxIncomingMsgLength uint32 = 1279

type packetReader struct{}

/*
 * ReadPacket reads a packet from a TCP connection. Performs the conversion
 * from network to local byte order.
 */
func (this *packetReader) ReadPacket(conn *net.TCPConn) (network.Packet, error) {
	msg := new(messages.Message)
	var err error

	// Read MsgType
	err = binary.Read(conn, binary.BigEndian, &msg.Type)
	if err != nil {
		return nil, fmt.Errorf("error while reading Message.Type: %v", err)
	}

	// Read message length
	err = binary.Read(conn, binary.BigEndian, &msg.Length)
	if err != nil {
		return nil, fmt.Errorf("error while reading Message.Length: %v", err)
	}

	if msg.Length == 0 {
		return nil, fmt.Errorf("invalid Message.Length: 0")
	}
	if msg.Length > MaxIncomingMsgLength {
		return nil, fmt.Errorf("invalid (too big) Message.Length: %v", msg.Length)
	}

	// Read payload
	msg.Payload = make([]byte, msg.Length, msg.Length)
	err = binary.Read(conn, binary.BigEndian, &msg.Payload)
	if err != nil {
		return nil, fmt.Errorf("error while reading payload: %v", err)
	}
	return msg, nil
}
