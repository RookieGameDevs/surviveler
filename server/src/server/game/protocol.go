/*
	Surviveler Protocol Implementation
	Implements the necessary interfaces for server.Server and server.Conn
*/
package game

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"github.com/ugorji/go/codec"
	"net"
	"server/network"
)

/*
 * value used to check the length of a client message before allocating
 * a buffer, in case the received size was wrong
 */
const MaxIncomingMsgLength uint32 = 1279

type MsgType uint16

/*
 * client -> server message
 */
type Message struct {
	Type   MsgType // the message type
	Length uint32  // the payload length
	Buffer []byte  // payload buffer
}

/*
 * ClientMessage is a message sent by the client, to which the server has added
 * the client Id
 */
type ClientMessage struct {
	*Message
	clientId uint16 // client Id (set by server)
}

/*
 * Serialize transforms a message into a byte slice
 */
func (msg Message) Serialize() []byte {
	// we know the buffer total size so we can provide it to our bytes.Buffer
	bbuf := bytes.NewBuffer(make([]byte, 0, 2+4+len(msg.Buffer)))
	binary.Write(bbuf, binary.BigEndian, msg.Type)
	binary.Write(bbuf, binary.BigEndian, msg.Length)
	binary.Write(bbuf, binary.BigEndian, msg.Buffer)

	return bbuf.Bytes()
}

/*
 * NewMessage creates a message from a message type and a generic payload
 */
func NewMessage(t MsgType, p interface{}) (*Message, error) {
	var mh codec.MsgpackHandle

	msg := new(Message)
	msg.Type = t

	// Encode payload to msgpack
	bb := new(bytes.Buffer)
	var enc *codec.Encoder = codec.NewEncoder(bb, &mh)
	err := enc.Encode(p)
	if err != nil {
		return nil, fmt.Errorf("Error encoding payload: %v\n", err)
	}

	// Copy the buffer
	msg.Buffer = bb.Bytes()

	// Length is the buffer length
	msg.Length = uint32(len(msg.Buffer))

	return msg, nil
}

type MsgReader struct{}

/*
 * ReadMessage reads a message from a TCP connection. Performs the conversion
 * from network to local byte order.
 */
func (this *MsgReader) ReadMessage(conn *net.TCPConn) (network.Message, error) {
	msg := new(Message)
	var err error

	// Read MsgType
	err = binary.Read(conn, binary.BigEndian, &msg.Type)
	if err != nil {
		return nil, fmt.Errorf("Error while reading Message.Type: %v", err)
	}

	// Read message length
	err = binary.Read(conn, binary.BigEndian, &msg.Length)
	if err != nil {
		return nil, fmt.Errorf("Error while reading Message.Length: %v", err)
	}

	if msg.Length == 0 {
		return nil, fmt.Errorf("Invalid Message.Length: 0")
	}
	if msg.Length > MaxIncomingMsgLength {
		return nil, fmt.Errorf("Invalid (too big) Message.Length: %v", msg.Length)
	}

	//  Read Payload Buffer
	msg.Buffer = make([]byte, msg.Length, msg.Length)
	err = binary.Read(conn, binary.BigEndian, &msg.Buffer)
	if err != nil {
		return nil, fmt.Errorf("Error while reading payload: %v", err)
	}
	return msg, nil
}
