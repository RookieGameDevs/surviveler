/*
 * Surviveler events package
 * event structure
 */
package events

//go:generate go-gencon -type Event -cont LockFreeQueue -name Queue
type Event struct {
	Type    EventType
	Payload interface{}
}

func NewEvent(eventType EventType, payload interface{}) *Event {
	evt := new(Event)
	evt.Type = eventType
	evt.Payload = payload
	return evt
}
