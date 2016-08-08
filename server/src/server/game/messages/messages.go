/*
 * Surviveler messages package
 * message implementation
 */
package messages

import (
	"bytes"
	"encoding/binary"

	log "github.com/Sirupsen/logrus"
	"github.com/ugorji/go/codec"
)

/*
 * value used to check the length of a client message before allocating
 * a buffer, in case the received size was wrong
 */
const MaxIncomingMsgLength uint32 = 1279

/*
 * Message represents an encoded message and its type
 */
type Message struct {
	Type    uint16 // the message type
	Length  uint32 // the payload length
	Payload []byte // payload buffer
}

/*
 * Serialize transforms a message into a byte slice
 */
func (msg Message) Serialize() []byte {
	// we know the payload total size so we can provide it to our bytes.Buffer
	bbuf := bytes.NewBuffer(make([]byte, 0, 2+4+len(msg.Payload)))
	binary.Write(bbuf, binary.BigEndian, msg.Type)
	binary.Write(bbuf, binary.BigEndian, msg.Length)
	binary.Write(bbuf, binary.BigEndian, msg.Payload)
	return bbuf.Bytes()
}

/*
 * New creates a new message from a message type and a generic payload
 */
func New(t uint16, p interface{}) *Message {
	var mh codec.MsgpackHandle
	msg := new(Message)
	msg.Type = t

	// Encode payload to msgpack
	bb := new(bytes.Buffer)
	var enc *codec.Encoder = codec.NewEncoder(bb, &mh)
	err := enc.Encode(p)
	if err != nil {
		log.WithError(err).Error("Error encoding payload")
		return nil
	}

	// Copy the payload buffer
	msg.Payload = bb.Bytes()

	// Length is the buffer length
	msg.Length = uint32(len(msg.Payload))

	return msg
}
