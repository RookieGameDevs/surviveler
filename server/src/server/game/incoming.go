/*
	Incoming Message
*/
package game

import (
	"encoding/binary"
	"fmt"
	"net"
	"server/core"
)

// value used to check the length of a client message before allocating
// a buffer, in case the received size was wrong
const MaxIncomingMsgLength uint16 = 0x4ff

type MsgType uint16

// client -> server message
type IncomingMsg struct {
	Length    uint16  // the message length (Length field excluded)
	Timestamp uint64  // message timestamp (emission time)
	Type      MsgType // the message type
	Buffer    []byte  // variable size buffer
}

func (inc IncomingMsg) Serialize() []byte {
	return nil
}

type IncomingMsgReader struct {
}

func (this *IncomingMsgReader) ReadMessage(conn *net.TCPConn) (core.Message, error) {

	in := new(IncomingMsg)
	var err error

	// Read message length
	err = binary.Read(conn, binary.BigEndian, &in.Length)
	if err != nil {
		return nil, fmt.Errorf("IncomingMsg.Length: %v", err)
	}
	fmt.Printf("IncomingMsg.Length: %v\n", in.Length)

	if in.Length == 0 {
		return nil, fmt.Errorf("Invalid IncomingMsg.Length: 0")
	}
	if in.Length > MaxIncomingMsgLength {
		return nil, fmt.Errorf("Invalid IncomingMsg.Length: (%v) > %v", in.Length, MaxIncomingMsgLength)
	}

	// Read Timestamp
	err = binary.Read(conn, binary.BigEndian, &in.Timestamp)
	if err != nil {
		return nil, fmt.Errorf("IncomingMsg.Timestamp: %v", err)
	}
	fmt.Printf("IncomingMsg.Timestamp: %v\n", in.Timestamp)

	// Read MsgType
	err = binary.Read(conn, binary.BigEndian, &in.Type)
	if err != nil {
		return nil, fmt.Errorf("IncomingMsg.Type: %v", err)
	}
	fmt.Printf("IncomingMsg.Type: %v\n", in.Type)

	/*
	 * Read Buffer (Total Length - various fields):
	 *- Timestamp + MsgType (8 + 2) = 10Bytes
	 */
	in.Buffer = make([]byte, in.Length-10, in.Length-10)
	_, err = conn.Read(in.Buffer)
	if err != nil {
		return nil, fmt.Errorf("IncomingMsg.Buffer: %v", err)
	}
	fmt.Printf("IncomingMsg.Buffer: %v\n", in.Buffer)
	return in, nil
}
