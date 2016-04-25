/*
	Outgoing Message
*/
package game

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"github.com/ugorji/go/codec"
)

// server -> client message
type OutgoingMsg struct {
	MsgType uint16 // the message type
	Length  uint32 // the msgpack payload length
	Buffer  []byte // variable size buffer
}

func (out OutgoingMsg) Serialize() []byte {

	// we know the buffer final size so we can provide it to our bytes.Buffer
	bbuf := bytes.NewBuffer(make([]byte, 0, 2+4+len(out.Buffer)))
	binary.Write(bbuf, binary.BigEndian, out.MsgType)
	binary.Write(bbuf, binary.BigEndian, out.Length)
	binary.Write(bbuf, binary.BigEndian, out.Buffer)

	return bbuf.Bytes()
}

type Pos struct{ Xpos, Ypos uint16 }

// NewOutgoingPosMsg creates a new Outgoing message representing a position
func NewOutgoingPosMsg(msgType uint16, pos Pos) (out *OutgoingMsg, err error) {

	out = new(OutgoingMsg)
	out.MsgType = msgType

	var mh codec.MsgpackHandle

	// Encode to msgpack
	bb := new(bytes.Buffer)
	var enc *codec.Encoder = codec.NewEncoder(bb, &mh)
	err = enc.Encode(pos)
	if err != nil {
		return nil, fmt.Errorf("Error encoding pos: %v\n", err)
	}

	// Encode to network byte order
	bbuf := bytes.NewBuffer(make([]byte, 0, len(bb.Bytes())))
	binary.Write(bbuf, binary.BigEndian, bb.Bytes())

	// Copy the buffer
	out.Buffer = bb.Bytes()

	// Length is the buffer length
	out.Length = uint32(len(out.Buffer))

	return out, nil
}
