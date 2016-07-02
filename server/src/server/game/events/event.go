/*
 * Surviveler events package
 * event structure
 */
package events

//go:generate go-gencon -type Event -cont LockFreeQueue -name EventQueue
type Event struct {
	Type    EventType
	Payload interface{}
}

func NewEvent(eventType EventType, payload interface{}) *Event {
	self := new(Event)
	self.Type = eventType
	self.Payload = payload
	return self
}
