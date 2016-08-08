/*
 * Surviveler protocol package
 * clients book-keeping
 */
package protocol

import (
	"server/game/messages"
	"server/network"
	"sync"
	"time"

	log "github.com/Sirupsen/logrus"
)

/*
 * ClientRegistry manages a list of connections to remote clients.
 *
 * It implements the Handshaker interface.
 */
type ClientRegistry struct {
	clients           map[uint32]*network.Conn // one for each client connection
	mutex             sync.RWMutex             // protect map from concurrent accesses
	allocId           func() uint32
	afterJoinHandler  AfterJoinHandler
	afterLeaveHandler AfterLeaveHandler
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
 * NewClientRegistry initializes and returns a ClientRegistry
 */
func NewClientRegistry(idAllocator func() uint32) *ClientRegistry {
	return &ClientRegistry{
		clients: make(map[uint32]*network.Conn, 0),
		allocId: idAllocator,
	}
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
	clientId = reg.allocId()
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
func (reg *ClientRegistry) Broadcast(msg *messages.Message) error {

	// protect client map access (read)
	reg.mutex.RLock()
	defer reg.mutex.RUnlock()

	for _, client := range reg.clients {
		// we tolerate only a very short delay
		err := client.AsyncSendPacket(msg, 10*time.Millisecond)
		if !client.IsClosed() {
			switch err {
			case network.ErrClosedConnection:
				// the connection could still have been closed in the meantime
				log.WithField("msg", msg).Warning("Client connection already closed")
			case network.ErrBlockingWrite:
				// this should not be tolerated, as we can't make the rest of the world wait
				log.WithError(err).WithField("msg", msg).Error("Blocking broadcast")
				return err
			}
		}
	}
	return nil
}

func (reg *ClientRegistry) Disconnect(id uint32, reason string) {
	// protect client map access (read)
	reg.mutex.RLock()
	defer reg.mutex.RUnlock()

	conn, ok := reg.clients[id]
	if !ok {
		log.WithField("client", id).Error("Uknown client id, can't disconnect him/her")
	}
	reg.Leave(reason, conn)
}

func (reg *ClientRegistry) Kick(id uint32, reason string) {
	// protect client map access (read)
	reg.mutex.RLock()
	defer reg.mutex.RUnlock()

	conn, ok := reg.clients[id]
	if !ok {
		log.WithField("client", id).Error("Unknown client id, can't kick him/her")
	}
	reg.Leave(reason, conn)
}

/*
 * ClientDataFunc is the type of functions accepting a ClientData and returning
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

/*
 * Leave sends a LEAVE message to the client associated to given connection
 */
func (reg *ClientRegistry) Leave(reason string, c *network.Conn) {
	clientData := c.GetUserData().(ClientData)

	// send LEAVE to client
	leave := messages.New(messages.LeaveId, messages.Leave{
		Id:     uint32(clientData.Id),
		Reason: reason,
	})
	if err := c.AsyncSendPacket(leave, 5*time.Millisecond); err != nil {
		// either the client received the LEAVE or not, we will close the
		// connection afterwards, so there's nothing more to do in order to
		// gracefully handle this error
		log.WithError(err).WithField("clientID", clientData.Id).Error("LEAVE message couldn't be sent")
	} else {
		log.WithField("clientID", clientData.Id).Info("LEAVE message has been sent")
	}

	// TODO: Remove this: the client should remain alive even when the connection
	// is closed. Example: when the lobby will be implemented

	// closes the connection, registry cleanup will be performed in OnClose
	go func() {
		time.Sleep(100 * time.Millisecond)
		if !c.IsClosed() {
			c.Close()
		}
	}()
}

func (reg *ClientRegistry) Join(join messages.Join, c *network.Conn) bool {
	clientData := c.GetUserData().(ClientData)

	log.WithFields(log.Fields{"name": join.Name, "clientData": clientData}).Info("Received JOIN from client")

	// client already JOINED?
	if clientData.Joined {
		reg.Leave("Joined already received", c)
		return false
	}

	// name length condition
	if len(join.Name) < 3 {
		reg.Leave("Name is too short", c)
		return false
	}

	// name already taken?
	nameTaken := false
	playerNames := make(map[uint32]string)

	// compute the list of joined players, populating the STAY message and
	// checking if name is taken as well
	reg.ForEach(func(cd ClientData) bool {
		nameTaken = cd.Name == join.Name
		playerNames[cd.Id] = cd.Name
		// stop iteration if name is taken
		return !nameTaken
	})

	if nameTaken {
		reg.Leave("Name is already taken", c)
		return false
	}

	// create and send STAY to the new client
	stay := messages.Stay{Id: clientData.Id, Players: playerNames}
	err := c.AsyncSendPacket(messages.New(messages.StayId, stay), time.Second)
	if err != nil {
		// handle error in case we couldn't send the STAY message
		log.WithError(err).Error("Couldn't send STAY message to the new client")
		reg.Leave("Couldn't finish handshaking", c)
		return false
	}

	// fill a JOINED message
	joined := &messages.Joined{
		Id:   clientData.Id,
		Name: join.Name,
		Type: join.Type,
	}

	log.WithField("joined", joined).Info("Tell to the world this client has joined")
	reg.Broadcast(messages.New(messages.JoinedId, joined))

	// at this point we consider the client as accepted
	clientData.Joined = true
	clientData.Name = join.Name
	c.SetUserData(clientData)
	return true
}

func (reg *ClientRegistry) AfterJoinHandler() AfterJoinHandler {
	return reg.afterJoinHandler
}

func (reg *ClientRegistry) SetAfterJoinHandler(fn AfterJoinHandler) {
	reg.afterJoinHandler = fn
}

func (reg *ClientRegistry) AfterLeaveHandler() AfterLeaveHandler {
	return reg.afterLeaveHandler
}

func (reg *ClientRegistry) SetAfterLeaveHandler(fn AfterLeaveHandler) {
	reg.afterLeaveHandler = fn
}
