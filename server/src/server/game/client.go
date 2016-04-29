package game

import (
	"fmt"
	"server/network"
)

type ClientRegistry struct {
	clients map[uint16]*network.Conn // one for each client connection
	nextId  uint16                   // next available client id (1 based)
}

// Init initializes the ClientRegistry
func (reg *ClientRegistry) Init() {
	reg.clients = make(map[uint16]*network.Conn, 0)
	reg.nextId = 0
}

// registerClient creates a new client and gives it an id
func (reg *ClientRegistry) registerClient(c *network.Conn) {
	// we have a new client, assign him an id.
	clientId := reg.nextId
	reg.clients[clientId] = c

	// record the client id inside the connection, this is needed for later
	// retriving the clientId when we just have a connection
	c.SetUserData(clientId)

	// Note: for now we just stupidly increment the next available id.
	//        We will have other problems to solve before this overflows...
	reg.nextId++
	fmt.Printf("Accepted a new client, id %v addr %v\n",
		clientId, c.GetRawConn().RemoteAddr())
}

// getClientId returns the client Id associated to a connection, or panic...
func (reg *ClientRegistry) getClientId(c *network.Conn) uint16 {
	// retrieve the client id from the connection
	clientId := c.GetUserData().(uint16)
	if _, ok := reg.clients[clientId]; !ok {
		panic(fmt.Sprintf("Unknown client id %v\n", clientId))
	}
	return clientId
}

// kick shouts "get the fuck out of my server now!"
func (reg *ClientRegistry) kick() {

	for k, v := range reg.clients {
		if !v.IsClosed() {
			fmt.Printf("Kicking client %v %v", k, v.GetRawConn().RemoteAddr())
			v.Close()
		}
	}
}
