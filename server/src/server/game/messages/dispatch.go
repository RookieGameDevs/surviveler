/*
 * Surviveler messages package
 * message dispatching & handling
 */
package messages

import (
//"server/game/messages"
)

/*
 * MessageHandler is the interface implemented by an object that handles messages.
 * The messages handled represents decoded payloads.
 */
type MessageHandler interface {
	handleMsg(interface{}, uint32) error
}

/*
 * MsgHandlerFunc is the type of function that handles messages. It
 * implements the MessageHandler interface.
 */
type MsgHandlerFunc func(interface{}, uint32) error

func (mhf MsgHandlerFunc) handleMsg(i interface{}, clientId uint32) error {
	return mhf(i, clientId)
}

/*
 * MessageManager keeps track of the message handlers objects
 */
type MessageManager struct {
	listeners map[uint16][]MessageHandler // registered listeners
	factory   *Factory                    // keep the msg factory
}

/*
 * Dispatch dispatches messages of a particular type to the listeners. It
 * performs the decoding of the payload into an interface.
 */
func (mm *MessageManager) Dispatch(msg *Message, clientId uint32) error {
	for _, handler := range mm.listeners[msg.Type] {
		iface := mm.factory.DecodePayload(msg.Type, msg.Payload)
		err := handler.handleMsg(iface, clientId)
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
		mm.factory = GetFactory()
	}
	mm.listeners[msgType] = append(mm.listeners[msgType], handler)
}
