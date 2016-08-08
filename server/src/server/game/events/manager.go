/*
 * Surviveler events package
 * event manager
 */
package events

type EventHandler func(*Event)

// Private helper type
type listenerMap map[EventType][]EventHandler

type Manager struct {
	queue     *Queue
	listeners listenerMap
}

func NewManager() *Manager {
	mgr := new(Manager)
	mgr.queue = NewQueue()
	mgr.listeners = make(listenerMap)
	return mgr
}

/*
 * registers an event handler for a specified event type.
 */
func (mgr *Manager) Subscribe(eventType EventType, callback EventHandler) {
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
func (mgr *Manager) Process() {
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

func (mgr *Manager) PostEvent(evt *Event) {
	mgr.queue.Enqueue(evt)
}
