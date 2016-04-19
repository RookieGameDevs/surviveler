/*
Definition of the basic message types
*/
package core

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"hash/adler32"
	"io"
)

// value used to check the length of a client message befoe allocating
// a buffer, in case the received size was wrong
const MaxClientMsgLength uint16 = 0xfff

// message header: 2 bytes
type MsgHeader struct {
	Length uint16 // Length of the whole msg without the Length field
}

// message footer: 4 bytes
type MsgFooter struct {
	Checksum uint32 // Checksum of the whole msg without Length and Checksum fields
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
	MsgFooter
}

// server -> client message
type OutgoingMsg struct {
	MsgHeader
	Timestamp   uint64 // message timestamp (emission time)
	Destination int16  // client Id
	Buffer      []byte // variable size buffer
	MsgFooter
}

func (in *IncomingMsg) Decode(reader io.Reader) error {

	var err error

	in.MsgHeader.Decode(reader)

	// Check length
	if in.Length > MaxClientMsgLength {
		return fmt.Errorf("Warning: Message Length(%v) > %v", in.Length, MaxClientMsgLength)
	}

	// Extract the needed number of bytes and fill the buffer with it
	msgbuf := make([]byte, in.Length, in.Length)
	_, err = reader.Read(msgbuf)
	if err != nil {
		return fmt.Errorf("ClientMsg.Decode: %v", err)
	}

	// Following reads will be performed on the buffer reader
	bufreader := bytes.NewReader(msgbuf)

	// Read Timestamp
	err = binary.Read(bufreader, binary.BigEndian, &in.Timestamp)
	if err != nil {
		return fmt.Errorf("ClientMsg.Timestamp: %v", in.Timestamp)
	}

	// Read Origin
	err = binary.Read(bufreader, binary.BigEndian, &in.Origin)
	if err != nil {
		return fmt.Errorf("ClientMsg.Origin: %v", in.Origin)
	}

	// Read MsgType
	err = binary.Read(bufreader, binary.BigEndian, &in.Type)
	if err != nil {
		return fmt.Errorf("ClientMsg.Type: %v", in.Type)
	}

	/*
	 * Read Buffer (Total Length - various fields):
	 *- Timestamp: 8B
	 *- Origin: 2B
	 *- MsgType: 2B
	 *- Checksum: 4B
	 *- Total: 16B
	 */
	in.Buffer = make([]byte, in.Length-16, in.Length-16)
	_, err = bufreader.Read(in.Buffer)
	if err != nil {
		return fmt.Errorf("Decoding ClientMsg, Reading ClientMsg.Buffer: ")
	}

	//fmt.Println(hex.Dump(in.Buffer))

	in.MsgFooter.Decode(bufreader)

	// Compute Checksum of the whole message (minus Checksum part)
	computed_checksum := adler32.Checksum(msgbuf[:in.Length-4])
	if computed_checksum != in.Checksum {
		return fmt.Errorf("Checksum error")
	}
	fmt.Println("Checksum OK")

	return nil
}

func (hdr *MsgHeader) Decode(reader io.Reader) error {

	var err error

	// read Length
	err = binary.Read(reader, binary.BigEndian, &hdr.Length)
	if err != nil {
		return fmt.Errorf("Decoding MsgHeader.Length: %v\n", err)
	}
	fmt.Printf("MsgHeader.Length: %v\n", hdr.Length)

	return nil
}

func (ftr *MsgFooter) Decode(reader io.Reader) error {

	var err error

	// read Checksum
	err = binary.Read(reader, binary.BigEndian, &ftr.Checksum)
	if err != nil {
		return fmt.Errorf("Decoding MsgFooter.Checksum: %v\n", err)
	}

	return nil
}
