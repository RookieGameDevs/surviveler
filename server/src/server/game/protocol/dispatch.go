/*
 * Surviveler protocol package
 * message dispatching & handling
 */
package protocol

import (
	"server/game/messages"
)

/*
 * MessageHandler is the interface implemented by an object that handles messages.
 * The messages handled represents decoded payloads.
 */
type MessageHandler interface {
	handleMsg(interface{}, uint16) error
}

/*
 * MsgHandlerFunc is the type of function that handles messages. It
 * implements the MessageHandler interface.
 */
type MsgHandlerFunc func(interface{}, uint16) error

func (mhf MsgHandlerFunc) handleMsg(i interface{}, clientId uint16) error {
	return mhf(i, clientId)
}

/*
 * MessageManager keeps track of the message handlers objects
 */
type MessageManager struct {
	listeners map[uint16][]MessageHandler // registered listeners
	factory   *messages.Factory           // keep the msg factory
}

/*
 * Dispatch dispatches messages of a particular type to the listeners. It
 * performs the decoding of the payload into an interface.
 */
func (mm *MessageManager) Dispatch(msg *Message, clientId uint16) error {
	handlers := mm.listeners[msg.Type]

	var err error
	var i interface{}
	for _, handler := range handlers {
		i, err = mm.factory.DecodePayload(msg.Type, msg.Buffer)
		if err != nil {
			return err
		}
		err = handler.handleMsg(i, clientId)
		if err != nil {
			return err
		}
	}
	return nil
}

/*
 * Listen registers an event handler for the listening of a particular type of
 * message
 */
func (mm *MessageManager) Listen(msgType uint16, handler MessageHandler) {
	if mm.listeners == nil {
		mm.listeners = make(map[uint16][]MessageHandler)
		mm.factory = messages.GetFactory()
	}
	mm.listeners[msgType] = append(mm.listeners[msgType], handler)
}
