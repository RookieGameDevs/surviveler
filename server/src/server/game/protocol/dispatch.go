/*
 * Surviveler protocol package
 * message dispatching & handling
 */
package protocol

/*
 * MessageHandler is the interface implemented by an object that handles messages
 */
type MessageHandler interface {
	handleMsg(Message, uint16) error
}

/*
 * MsgHandlerFunc is the type of function that handles messages. It
 * implementes the MessageHandler interface
 */
type MsgHandlerFunc func(Message, uint16) error

func (mhf MsgHandlerFunc) handleMsg(msg Message, clientId uint16) error {
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
func (mm *MessageManager) Dispatch(msg Message, clientId uint16) {
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
