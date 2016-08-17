/*
 * Surviveler events package
 * event structure
 */
package events

//go:generate go-gencon -type Event -cont LockFreeQueue -name Queue
type Event struct {
	Type    Type
	Payload interface{}
}

func NewEvent(eventType Type, payload interface{}) *Event {
	evt := new(Event)
	evt.Type = eventType
	evt.Payload = payload
	return evt
}
