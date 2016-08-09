/*
 * Surviveler protocol package
 * server implementation
 */
package protocol

import (
	"net"
	"server/game/messages"
	"server/network"
	"sync"
	"time"

	log "github.com/Sirupsen/logrus"
)

const (
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

type (
	messageHandler func(c *network.Conn, msg interface{}) error
)

/*
 * Server represents a TCP server. It implements the network.ConnEvtHandler
 * interface.
 */
type Server struct {
	port           string
	server         network.Server                   // tcp server instance
	clients        *ClientRegistry                  // manage the connected clients
	telnet         *TelnetServer                    // embedded telnet server
	factory        *messages.Factory                // the unique message factory
	wg             *sync.WaitGroup                  // game wait group
	handshaker     Handshaker                       // handle handshaking
	msgHandlers    map[messages.Type]messageHandler // message handlers
	playerJoinedCb func(uint32, uint8)              // raised after a successfull JOIN
	playerLeftCb   func(uint32)                     // raised after an effective LEAVE
}

/*
 * NewServer returns a new configured Server instance
 */
func NewServer(port string, clients *ClientRegistry,
	telnet *TelnetServer, wg *sync.WaitGroup, handshaker Handshaker) *Server {

	return &Server{
		clients:     clients,
		port:        port,
		telnet:      telnet,
		factory:     messages.GetFactory(),
		wg:          wg,
		msgHandlers: make(map[messages.Type]messageHandler),
		handshaker:  handshaker,
	}
}

/*
 * RegisterMsgHandler registers a handler for incoming message
 */
func (srv *Server) RegisterMsgHandler(t messages.Type, fn messageHandler) {
	srv.msgHandlers[t] = fn
}

/*
 * listenTo resolves and listens to a tcp address, returns the listener
 */
func listenTo(addr string) (*net.TCPListener, error) {
	tcpAddr, err := net.ResolveTCPAddr("tcp4", addr)
	if err != nil {
		log.WithError(err).Warn("couldn't resolve address")
		return nil, err
	}
	listener, err := net.ListenTCP("tcp", tcpAddr)
	if err != nil {
		log.WithError(err).Warn("couldn't initiate TCP listening")
		return nil, err
	}
	return listener, nil
}

/*
 * Start creates the TCP server and starts the listening goroutine
 */
func (srv *Server) Start() {
	// creates a server
	config := &network.ServerCfg{
		MaxOutgoingChannels: MAX_OUT_CHANNELS,
		MaxIncomingChannels: MAX_IN_CHANNELS,
	}
	srv.server = *network.NewServer(config, srv, &packetReader{})

	listener, err := listenTo(":" + srv.port)
	if err != nil {
		log.Fatal("can't start server")
	}

	// starts the server in a listening goroutine
	srv.wg.Add(1)
	go srv.server.Start(listener, time.Second)
	log.WithField("addr", listener.Addr()).Info("Server ready, listening for incoming connections")

	if srv.telnet != nil {
		// start telnet server if present
		listener, err := listenTo(":" + srv.telnet.port)
		if err != nil {
			log.Fatal("can't start telnet server")
		}
		srv.telnet.Start(listener, srv.wg)
		registerTelnetCommands(srv.telnet, srv.clients)
	}
}

/*
 * OnConnect gets called by the server at connection initialization, once by
 * connection. This gives us the chance to register a new client and perform
 * the client initialization
 */
func (srv *Server) OnConnect(c *network.Conn) bool {
	// register our new client connection
	// this is not the same as accepting the player
	srv.clients.register(c)
	return true
}

/*
 * OnIncomingMsg gets called by the server each time a message has been read
 * from the connection
 */
func (srv *Server) OnIncomingPacket(c *network.Conn, packet network.Packet) bool {
	clientData := c.GetUserData().(ClientData)
	raw := packet.(*messages.Message)

	log.WithFields(
		log.Fields{
			"clientData": clientData,
			"addr":       c.GetRawConn().RemoteAddr(),
			"type":       raw.Type.String(),
		}).Debug("Incoming message")

	// decode the raw message
	msg := srv.factory.Decode(raw)

	// get handler
	handler, ok := srv.msgHandlers[raw.Type]
	if ok {
		if err := handler(c, msg); err != nil {
			log.WithError(err).Error("Error handling message")
			return false
		}
	} else {

		switch raw.Type {

		case messages.PingId:

			// immediately reply pong
			ping := msg.(messages.Ping)
			pong := messages.New(messages.PongId,
				messages.Pong{
					Id:     ping.Id,
					Tstamp: time.Now().UnixNano() / int64(time.Millisecond),
				})
			if err := c.AsyncSendPacket(pong, time.Second); err != nil {
				log.WithError(err).Error("Error handling message")
				return false
			}

		case messages.JoinId:

			join := msg.(messages.Join)
			// JOIN is handled by the handshaker
			if srv.handshaker.Join(join, c) {
				// new client has been accepted
				if srv.playerJoinedCb != nil {
					// raise 'player joined' external callback
					srv.playerJoinedCb(clientData.Id, join.Type)
				}
			}
		}
	}

	return true
}

/*
 * OnClose gets called by the server at connection closing, once by
 * connection. This gives us the chance to unregister a new client and perform
 * client cleanup
 */
func (srv *Server) OnClose(c *network.Conn) {
	log.WithField("addr", c.GetRawConn().RemoteAddr()).Debug("Connection closed")

	// unregister the client before anything
	clientData := c.GetUserData().(ClientData)
	srv.clients.unregister(clientData.Id)

	if clientData.Joined {
		// client is still JOINED so that's a disconnection initiated externally
		// send a LEAVE to the rest of the world
		msg := messages.New(messages.LeaveId,
			messages.Leave{
				Id:     uint32(clientData.Id),
				Reason: "client disconnection",
			})
		srv.Broadcast(msg)
	} else {
		// the client was not marked as JOINED, so nobody knows about him
		// and we have nothing more to do
	}

	if srv.playerLeftCb != nil {
		// raise 'player left' external callback
		srv.playerLeftCb(clientData.Id)
	}
}

// OnPlayerJoined sets the function called when a player has joined the game
func (srv *Server) OnPlayerJoined(fn func(ID uint32, playerType uint8)) {
	srv.playerJoinedCb = fn
}

// OnPlayerJoined sets the function called when a player has left the game
func (srv *Server) OnPlayerLeft(fn func(ID uint32)) {
	srv.playerLeftCb = fn
}

/*
 * Broadcast sends a message to all clients
 */
func (srv *Server) Broadcast(msg *messages.Message) error {
	err := srv.clients.Broadcast(msg)
	if err != nil {
		log.WithError(err).Error("Couldn't broadcast")
	}
	return err
}

/*
 * Stop stops the tcp server and the clients connections
 */
func (srv *Server) Stop() {
	log.Info("Stopping server")
	srv.server.Stop()
	srv.wg.Done()
}
