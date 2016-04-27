package game

import (
	"fmt"
	"github.com/ugorji/go/codec"
	"reflect"
)

// Types of messages sent by the client
const (
	PingId MsgType = 0 + iota
	PongId
	PositionId
)

type MsgFactory struct {
	registry map[MsgType]reflect.Type
}

// NewMsgFactory instantiates a new MsgFactory
func NewMsgFactory() *MsgFactory {
	mf := new(MsgFactory)
	mf.registry = make(map[MsgType]reflect.Type)
	return mf
}

// RegisterMsgType registers a new MsgType and associates it to a struct type
func (mf MsgFactory) RegisterMsgType(t MsgType, i interface{}) {

	// retrieve underlying msg type
	it := reflect.TypeOf(i)
	mf.registry[t] = it
}

func (mf MsgFactory) NewMsg(t MsgType) interface{} {

	if it, ok := mf.registry[t]; ok {
		return reflect.New(it).Elem().Interface()
	}
	panic(fmt.Sprintf("MsgFactory: MsgType %v not found\n", t))
}

func (mf MsgFactory) DecodePayload(t MsgType, p []byte) (interface{}, error) {

	var mh codec.MsgpackHandle

	// Create a struct having the corresponding underlying type
	msg := mf.NewMsg(t)

	// Decode msgpack payload into interface
	var dec *codec.Decoder = codec.NewDecoderBytes(p, &mh)
	err := dec.Decode(&msg)
	if err != nil {
		return nil, fmt.Errorf("Error decoding payload: %v\n", err)
	}

	return msg, nil
}

// PositionMsg represents a position in 2D space
type PositionMsg struct{ Xpos, Ypos uint16 }

// Client -> Server time sync message
type PingMsg struct {
	Id     uint32
	Tstamp int64
}

// Server -> Client time sync message
type PongMsg struct {
	Id     uint32
	Tstamp int64
}
