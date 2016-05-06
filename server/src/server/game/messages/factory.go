/*
 * Surviveler messages package
 * message factory
 */
package messages

import (
	log "github.com/Sirupsen/logrus"
	"github.com/ugorji/go/codec"
	"reflect"
)

var factory *Factory

/*
 * Factory associates unique message ids with their corresponding message
 * structures. Once every know message has been registered with RegisterMsgType,
 * a new message struct can be instantiated by passing its type to
 * Factory.NewMsg()
 */
type Factory struct {
	registry map[uint16]reflect.Type
}

/*
 * GetFactory returns the global message factory, instaniating it at first call
 */
func GetFactory() *Factory {
	if factory == nil {
		factory = new(Factory)
		factory.registry = make(map[uint16]reflect.Type)
		factory.registerMsgTypes()
	}
	return factory
}

/*
 * registerMsgTypes associates each message id with their corresponding message
 * struct type
 */
func (mf Factory) registerMsgTypes() {
	mf.registerMsgType(PingId, PingMsg{})
	mf.registerMsgType(PongId, PongMsg{})
	mf.registerMsgType(GameStateId, GameStateMsg{})
	mf.registerMsgType(AddPlayerId, AddPlayerMsg{})
	mf.registerMsgType(DelPlayerId, DelPlayerMsg{})
}

/*
 * registerMsgType registers a new MsgType and associates it to a struct type
 */
func (mf Factory) registerMsgType(t uint16, i interface{}) {
	// retrieve underlying msg type
	it := reflect.TypeOf(i)
	mf.registry[t] = it
}

/*
 * newMsg returns a new (zero'ed) message struct
 */
func (mf Factory) newMsg(t uint16) interface{} {
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
func (mf Factory) DecodePayload(t uint16, p []byte) (interface{}, error) {
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
