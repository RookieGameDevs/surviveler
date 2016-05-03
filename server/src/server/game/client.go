package game

import (
	log "github.com/Sirupsen/logrus"
	"server/network"
	"sync"
	"time"
)

type ClientRegistry struct {
	clients map[uint16]*network.Conn // one for each client connection
	nextId  uint16                   // next available client id (1 based)
	mutex   sync.RWMutex             // protect from concurrent map accesses (data races)
}

/*
 * Init initializes the ClientRegistry
 */
func (reg *ClientRegistry) init() {
	reg.clients = make(map[uint16]*network.Conn, 0)
	reg.nextId = 0
}

/*
 * register creates a new client, gives it an id and return the id
 */
func (reg *ClientRegistry) register(client *network.Conn) uint16 {
	var clientId uint16

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
	client.SetUserData(clientId)

	// Note: for now we just stupidly increment the next available id.
	//        We will have other problems to solve before this overflows...
	reg.mutex.Unlock()

	log.WithFields(log.Fields{
		"id":   clientId,
		"addr": client.GetRawConn().RemoteAddr(),
	}).Info("Accepted a new client")

	return clientId
}

/*
 * sendAll sends a message to all clients
 */
func (reg *ClientRegistry) sendAll(msg *Message) error {

	// protect client map access (read)
	reg.mutex.RLock()
	for _, client := range reg.clients {
		// check connection state
		if !client.IsClosed() {
			err := client.AsyncSendMessage(msg, time.Millisecond)
			// TODO: check out error type, blocking write or connection closed?
			// the connection could still have been closed by the client here
			if err != nil {
				log.WithError(err).WithField("msg", msg).Error("Error sending message")
				return err
			}
		}
	}
	reg.mutex.RUnlock()
	return nil
}
