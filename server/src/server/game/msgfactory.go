/*
 * Surviveler Message Factory
 */
package game

import (
	log "github.com/Sirupsen/logrus"
	"github.com/ugorji/go/codec"
	"reflect"
)

/*
 * MsgFactory associates unique message ids with their corresponding message
 * structures. Once every know message has been registered with RegisterMsgType,
 * a new message struct can be instantiated by passing its type to
 * MsgFactory.NewMsg()
 */
type MsgFactory struct {
	registry map[MsgType]reflect.Type
}

/*
 * NewMsgFactory instantiates a new MsgFactory
 */
func NewMsgFactory() *MsgFactory {
	mf := new(MsgFactory)
	mf.registry = make(map[MsgType]reflect.Type)
	return mf
}

/*
 * Register all message types
 */
func (mf MsgFactory) RegisterMsgTypes() {
	mf.registerMsgType(PingId, PingMsg{})
	mf.registerMsgType(PongId, PongMsg{})
	mf.registerMsgType(GameStateId, GameStateMsg{})
	mf.registerMsgType(NewPlayerId, NewPlayerMsg{})
}

/*
 * registerMsgType registers a new MsgType and associates it to a struct type
 */
func (mf MsgFactory) registerMsgType(t MsgType, i interface{}) {
	// retrieve underlying msg type
	it := reflect.TypeOf(i)
	mf.registry[t] = it
}

/*
 * newMsg returns a new (zero'ed) message struct
 */
func (mf MsgFactory) newMsg(t MsgType) interface{} {
	var it reflect.Type
	var ok bool
	if it, ok = mf.registry[t]; !ok {
		log.WithField("msgtype", t).Panic("Unknown message type")
	}
	return reflect.New(it).Elem().Interface()
}

/*
 * DecodePayload returns a new message struct, decoded from given payload
 */
func (mf MsgFactory) DecodePayload(t MsgType, p []byte) (interface{}, error) {
	var mh codec.MsgpackHandle
	// Create a struct having the corresponding underlying type
	msg := mf.newMsg(t)

	// Decode msgpack payload into interface
	var dec *codec.Decoder = codec.NewDecoderBytes(p, &mh)
	err := dec.Decode(&msg)
	if err != nil {
		log.WithError(err).Error("Couldn't decode payload")
		return nil, err
	}

	return msg, nil
}
