/*
Definition of the basic message types
*/
package core

import (
	"encoding/binary"
	"fmt"
	"io"
)

// value used to check the length of a client message before allocating
// a buffer, in case the received size was wrong
const MaxIncomingMsgLength uint16 = 0x4ff

// message header: 2 bytes
type MsgHeader struct {
	Length uint16 // Length of the whole msg without the Length field
}

// Message Type
type MsgType uint16

// client -> server message
type IncomingMsg struct {
	MsgHeader
	Timestamp uint64  // message timestamp (emission time)
	Origin    int16   // client Id
	Type      MsgType // the message type
	Buffer    []byte  // variable size buffer
}

// server -> client message
type OutgoingMsg struct {
	MsgHeader
	Timestamp   uint64 // message timestamp (emission time)
	Destination int16  // client Id
	Buffer      []byte // variable size buffer
}

// Decode reads a stream and decodes it into an IncomingMsg struct
func (in *IncomingMsg) Decode(reader io.Reader) error {

	var err error

	// Decode header, fail if decoded length is invalid
	in.MsgHeader.Decode(reader)
	if in.Length > MaxIncomingMsgLength {
		return fmt.Errorf("Invalid IncomingMsg.Length: (%v) > %v", in.Length, MaxIncomingMsgLength)
	}

	// Read Timestamp
	err = binary.Read(reader, binary.BigEndian, &in.Timestamp)
	if err != nil {
		return fmt.Errorf("IncomingMsg.Timestamp: %v", err)
	}

	// Read Origin
	err = binary.Read(reader, binary.BigEndian, &in.Origin)
	if err != nil {
		return fmt.Errorf("IncomingMsg.Origin: %v", err)
	}

	// Read MsgType
	err = binary.Read(reader, binary.BigEndian, &in.Type)
	if err != nil {
		return fmt.Errorf("IncomingMsg.Type: %v", err)
	}

	/*
	 * Read Buffer (Total Length - various fields):
	 *- Timestamp + Origin + MsgType (8 + 2 + 2) = 12Bytes
	 */
	in.Buffer = make([]byte, in.Length-12, in.Length-12)
	_, err = reader.Read(in.Buffer)
	if err != nil {
		return fmt.Errorf("IncomingMsg.Buffer: %v", err)
	}

	return nil
}

// Decode reads a stream and decodes it into an MsgHeader struct
func (hdr *MsgHeader) Decode(reader io.Reader) error {

	var err error

	// read Length
	err = binary.Read(reader, binary.BigEndian, &hdr.Length)
	if err != nil {
		return fmt.Errorf("MsgHeader.Length: %v", err)
	}

	return nil
}
