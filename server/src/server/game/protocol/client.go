/*
 * Surviveler protocol package
 * clients book-keeping
 */
package protocol

import (
	log "github.com/Sirupsen/logrus"
	"server/network"
	"sync"
	"time"
)

/*
 * ClientRegistry manages a list of connections to remote clients
 */
type ClientRegistry struct {
	clients map[uint32]*network.Conn // one for each client connection
	nextId  uint32                   // next available client id (1 based)
	mutex   sync.RWMutex             // protect map from concurrent accesses
}

/*
 * ClientData contains the fields associated to a connection
 */
type ClientData struct {
	Id     uint32
	Name   string
	Joined bool
}

/*
 * Init initializes the ClientRegistry
 */
func (reg *ClientRegistry) init() {
	reg.clients = make(map[uint32]*network.Conn, 0)
	reg.nextId = 0
}

/*
 * register creates a new client, assigns it an id and returns it
 */
func (reg *ClientRegistry) register(client *network.Conn) uint32 {
	var clientId uint32

	// protect:
	// - increment the next available id
	// - client map write
	reg.mutex.Lock()

	// we have a new client, assign him an id.
	clientId = reg.nextId
	reg.nextId++
	reg.clients[clientId] = client

	// record the client id inside the connection, this is needed for later
	// retriving the clientId when we just have a connection
	clientData := ClientData{
		Id:     clientId,
		Name:   "",
		Joined: false,
	}
	client.SetUserData(clientData)

	// Note: for now we just stupidly increment the next available id.
	//        We will have other problems to solve before this overflows...
	reg.mutex.Unlock()

	log.WithFields(log.Fields{
		"client": clientData,
		"addr":   client.GetRawConn().RemoteAddr(),
	}).Info("Accepted a new client")

	return clientId
}

/*
 * unregister removes client from the registry
 */
func (reg *ClientRegistry) unregister(clientId uint32) {
	log.WithField("id", clientId).Debug("Unregister a client")
	// protect client map write
	reg.mutex.Lock()
	delete(reg.clients, clientId)
	reg.mutex.Unlock()
}

/*
 * Broadcast sends a message to all clients
 */
func (reg *ClientRegistry) Broadcast(msg *Message) error {

	// protect client map access (read)
	reg.mutex.RLock()
	defer reg.mutex.RUnlock()

	for _, client := range reg.clients {
		// we tolerate only a very short delay
		err := client.AsyncSendMessage(msg, 5*time.Millisecond)
		if !client.IsClosed() {
			switch err {
			case network.ErrClosedConnection:
				// the connection could still have been closed in the meantime
				log.WithField("msg", msg).Warning("Client connection already closed")
			case network.ErrBlockingWrite:
				// this should not be tolerated, as we can make the rest of the world wait
				log.WithError(err).WithField("msg", msg).Error("Blocking broadcast")
				return err
			}
		}
	}
	return nil
}

/*
 * ClientDataFunc is the type of functions accetping a ClientData and returning
 * a boolean.
 */
type ClientDataFunc func(ClientData) bool

/*
 * ForEach runs a provided function, once per each connection, and gives it a
 * copy of the ClientData struct associated to the current connection. The
 * callback method should not call any ClientRegistry. it is guaranteed that the
 * list of connection won't be modified during the ForEach closure. ForEach exits
 * prematurely if the callback returns false.
 */
func (reg *ClientRegistry) ForEach(cb ClientDataFunc) {

	// protect client map access (read)
	reg.mutex.RLock()
	defer reg.mutex.RUnlock()
	for _, client := range reg.clients {
		if !cb(client.GetUserData().(ClientData)) {
			break
		}
	}
}
