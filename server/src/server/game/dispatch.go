/*
 * Surviveler game package
 * message dispatching & handling
 */
package game

import (
	"server/game/protocol"
)

/*
 * MessageHandler is the interface implemented by an object that handles messages
 */
type MessageHandler interface {
	handleMsg(protocol.Message, uint16) error
}

/*
 * MsgHandlerFunc is the type of functions that handles messages. It
 * implementes the MessageHandler interface
 */
type MsgHandlerFunc func(protocol.Message, uint16) error

func (mhf MsgHandlerFunc) handleMsg(msg protocol.Message, clientId uint16) error {
	return mhf(msg, clientId)
}

/*
 * MessageManager keeps track of the message handlers objects
 */
type MessageManager struct {
	listeners map[uint16][]MessageHandler
}

/*
 * Dispatch dispatches messages of a particular type to the listeners
 */
func (mm *MessageManager) Dispatch(msg protocol.Message, clientId uint16) {
	handlers := mm.listeners[msg.Type]

	for _, handler := range handlers {
		handler.handleMsg(msg, clientId)
	}
}

func (mm *MessageManager) Listen(msgType uint16, handler MessageHandler) {
	if mm.listeners == nil {
		mm.listeners = make(map[uint16][]MessageHandler)
	}
	mm.listeners[msgType] = append(mm.listeners[msgType], handler)
}
