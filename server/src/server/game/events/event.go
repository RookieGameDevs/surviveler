/*
 * Surviveler events package
 * event structure
 */
package events

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
