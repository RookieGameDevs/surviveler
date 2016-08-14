/*
 * Surviveler messages package
 * message factory
 */
package messages

import (
	"reflect"

	log "github.com/Sirupsen/logrus"
	"github.com/ugorji/go/codec"
)

var factory *Factory

/*
 * Factory associates unique message ids with the corresponding message
 * structures. Once a message has been registered, a message struct can
 * be instantiated by passing its type to newMsg()
 */
type Factory struct {
	registry map[Type]reflect.Type
}

/*
 * GetFactory returns the global message factory, instantiating it at first call
 */
func GetFactory() *Factory {
	if factory == nil {
		factory = new(Factory)
		factory.registry = make(map[Type]reflect.Type)
		factory.registerMsgTypes()
	}
	return factory
}

/*
 * registerMsgTypes associates each message id with their corresponding message
 * struct type
 */
func (mf Factory) registerMsgTypes() {
	// client/server message types
	mf.registerMsgType(PingId, Ping{})
	mf.registerMsgType(PongId, Pong{})
	mf.registerMsgType(GameStateId, GameState{})
	mf.registerMsgType(MoveId, Move{})
	mf.registerMsgType(BuildId, Build{})
	mf.registerMsgType(JoinId, Join{})
	mf.registerMsgType(JoinedId, Joined{})
	mf.registerMsgType(StayId, Stay{})
	mf.registerMsgType(LeaveId, Leave{})
	mf.registerMsgType(RepairId, Repair{})
	mf.registerMsgType(AttackId, Attack{})
	mf.registerMsgType(OperateId, Operate{})
}

/*
 * registerMsgType registers a new MsgType and associates it to a struct type
 */
func (mf Factory) registerMsgType(t Type, i interface{}) {
	// retrieve underlying msg type
	it := reflect.TypeOf(i)
	mf.registry[t] = it
}

/*
 * newMsg returns a new (zero'ed) message struct
 */
func (mf Factory) newMsg(t Type) interface{} {
	var ok bool
	var reft reflect.Type
	if reft, ok = mf.registry[t]; !ok {
		log.WithField("msgtype", t).Error("Unknown message type")
	}
	return reflect.New(reft).Elem().Interface()
}

/*
 * Decode returns a new specialized message, decoded from a raw message
 */
func (mf Factory) Decode(raw *Message) interface{} {
	var mh codec.MsgpackHandle
	// create a struct having the corresponding underlying type
	msg := mf.newMsg(raw.Type)

	// decode msgpack payload into interface
	decoder := codec.NewDecoderBytes(raw.Payload, &mh)
	err := decoder.Decode(&msg)
	if err != nil {
		log.WithError(err).Error("Couldn't decode raw message payload")
	}
	return msg
}
