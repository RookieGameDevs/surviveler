/*
 * Surviveler events package
 * event manager
 */
package events

type EventHandler func(*Event)

// Private helper type
type listenerMap map[EventType][]EventHandler

type EventManager struct {
	queue     *Queue
	listeners listenerMap
}

func NewEventManager() *EventManager {
	mgr := new(EventManager)
	mgr.queue = NewQueue()
	mgr.listeners = make(listenerMap)
	return mgr
}

/*
 * registers an event handler for a specified event type.
 */
func (mgr *EventManager) Subscribe(eventType EventType, callback EventHandler) {
	lst, ok := mgr.listeners[eventType]
	if !ok {
		lst = make([]EventHandler, 0)
	}
	mgr.listeners[eventType] = append(lst, callback)
}

/*
 * Process processes every event in the event queue.
 *
 * This method dequeues and processes sequentially every event, thus blocking
 * until all events have been processed.
 */
func (mgr *EventManager) Process() {
	for {
		if evt, found := mgr.queue.Dequeue(); found {
			lst, ok := mgr.listeners[evt.Type]
			if ok {
				for _, callback := range lst {
					callback(evt)
				}
			}
		} else {
			break
		}
	}
}

func (mgr *EventManager) PostEvent(evt *Event) {
	mgr.queue.Enqueue(evt)
}
