package game

import (
	log "github.com/Sirupsen/logrus"
	"server/network"
	"sync"
)

type ClientRegistry struct {
	clients map[uint16]*network.Conn // one for each client connection
	nextId  uint16                   // next available client id (1 based)
	mutex   sync.Mutex               // protect from concurrent map accesses (data races)
}

/*
 * Init initializes the ClientRegistry
 */
func (reg *ClientRegistry) Init() {
	reg.clients = make(map[uint16]*network.Conn, 0)
	reg.nextId = 0
}

/*
 * registerClient creates a new client and gives it an id
 */
func (reg *ClientRegistry) registerClient(client *network.Conn) {
	var clientId uint16

	// protect :
	// - increment of the next available id
	// - client map access
	reg.mutex.Lock()

	// we have a new client, assign him an id.
	clientId = reg.nextId
	reg.clients[clientId] = client

	// record the client id inside the connection, this is needed for later
	// retriving the clientId when we just have a connection
	client.SetUserData(clientId)

	// Note: for now we just stupidly increment the next available id.
	//        We will have other problems to solve before this overflows...
	reg.nextId++
	reg.mutex.Unlock()

	log.WithFields(log.Fields{
		"id":   clientId,
		"addr": client.GetRawConn().RemoteAddr(),
	}).Info("Accepted a new client")
}

/*
 * getClientId returns the client Id associated to a connection, or panic...
 */
func (reg *ClientRegistry) getClientId(c *network.Conn) uint16 {
	// retrieve the client id from the connection
	clientId := c.GetUserData().(uint16)

	// protect client map access
	reg.mutex.Lock()
	if _, ok := reg.clients[clientId]; !ok {
		log.WithField("id", clientId).Panic("Unknown client")
	}
	reg.mutex.Unlock()
	return clientId
}

/*
 * kick says out loud "get the fuck out of my server now!"
 */
func (reg *ClientRegistry) kickClient(clientId uint16) {
	log.WithField("id", clientId).Debug("About to kick client")

	// protect client map access
	reg.mutex.Lock()
	client, ok := reg.clients[clientId]
	if !ok {
		log.WithField("id", clientId).Panic("Unknown client")
	}
	client.Close()
	reg.mutex.Unlock()

	log.WithFields(log.Fields{
		"id":   clientId,
		"addr": client.GetRawConn().RemoteAddr(),
	}).Info("Kicked client")
}
