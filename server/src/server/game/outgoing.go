/*
	Outgoing Message
*/
package game

import (
	"bytes"
	"encoding/binary"
)

// server -> client message
type OutgoingMsg struct {
	Length    uint16 // the message length (Length field excluded)
	Timestamp uint64 // message timestamp (emission time)
	Buffer    []byte // variable size buffer
}

func (out OutgoingMsg) Serialize() []byte {

	// we know the buffer final size so we can provide it to our bytes.Buffer
	bbuf := bytes.NewBuffer(make([]byte, 0, 2+8+len(out.Buffer)))
	binary.Write(bbuf, binary.BigEndian, out.Length)
	binary.Write(bbuf, binary.BigEndian, out.Timestamp)
	binary.Write(bbuf, binary.BigEndian, out.Buffer)

	return bbuf.Bytes()
}
