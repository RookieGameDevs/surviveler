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
 * registerClient creates a new client, gives it an id and return the id
 */
func (reg *ClientRegistry) registerClient(client *network.Conn) uint16 {
	var clientId uint16

	// protect:
	// - increment the next available id
	// - client map write
	reg.mutex.Lock()

	// we have a new client, assign him an id.
	clientId = reg.nextId
	reg.nextId++
	reg.clients[clientId] = client

	// Note: for now we just stupidly increment the next available id.
	//        We will have other problems to solve before this overflows...
	reg.mutex.Unlock()

	// record the client id inside the connection, this is needed for later
	// retriving the clientId when we just have a connection
	client.SetUserData(clientId)

	log.WithFields(log.Fields{
		"id":   clientId,
		"addr": client.GetRawConn().RemoteAddr(),
	}).Info("Accepted a new client")

	return clientId
}

/*
 * getClientId returns the client Id associated to a connection, or panic...
 */
func (reg *ClientRegistry) getClientId(c *network.Conn) uint16 {
	// retrieve the client id from the connection
	clientId := c.GetUserData().(uint16)

	// protect client map access
	reg.mutex.RLock()
	if _, ok := reg.clients[clientId]; !ok {
		log.WithField("id", clientId).Panic("Unknown client")
	}
	reg.mutex.RUnlock()
	return clientId
}

/*
 * kick closes a client connection and removes it from the registry
 */
func (reg *ClientRegistry) kickClient(clientId uint16) {
	log.WithField("id", clientId).Debug("About to kick client")

	// protect client map access
	reg.mutex.Lock()
	client, ok := reg.clients[clientId]
	if !ok {
		log.WithField("id", clientId).Panic("Unknown client")
	}
	delete(reg.clients, clientId)
	reg.mutex.Unlock()

	client.Close()

	log.WithFields(log.Fields{
		"id":   clientId,
		"addr": client.GetRawConn().RemoteAddr(),
	}).Info("Kicked client")
}

/*
 * kickAll says out loud "get the fuck out of my server now!"
 */
func (reg *ClientRegistry) kickAll() {
	log.Debug("About to kick all clients")

	// protect client map access
	reg.mutex.Lock()
	for _, client := range reg.clients {
		client.Close()
	}
	reg.mutex.Unlock()

	log.Info("Kicked everybody out")
}
