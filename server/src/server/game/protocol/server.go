/*
 * Surviveler protocol package
 * server implementation
 */
package protocol

import (
	log "github.com/Sirupsen/logrus"
	"net"
	"server/game/messages"
	"server/network"
	"sync"
	"time"
)

const (
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

type MsgCallbackFunc func(msg *messages.Message, clientId uint32) error

/*
 * Server represents a TCP server. It implements the network.ConnEvtHandler
 * interface.
 */
type Server struct {
	port          string
	server        network.Server    // tcp server instance
	clients       ClientRegistry    // manage the connected clients
	msgcb         MsgCallbackFunc   // incoming messages callback
	telnet        *TelnetServer     // embedded telnet server
	factory       *messages.Factory // the unique message factory
	gameWaitGroup *sync.WaitGroup   // game wait group
}

/*
 * NewServer returns a new configured Server instance
 */
func NewServer(port string, msgcb MsgCallbackFunc, clients *ClientRegistry, telnet *TelnetServer, waitGroup *sync.WaitGroup) *Server {
	return &Server{
		clients:       *clients,
		msgcb:         msgcb,
		port:          port,
		telnet:        telnet,
		factory:       messages.GetFactory(),
		gameWaitGroup: waitGroup,
	}
}

/*
 * Start creates the TCP server and starts the listening goroutine
 */
func (srv *Server) Start() {
	// creates a tcp listener
	tcpAddr, err := net.ResolveTCPAddr("tcp4", ":"+srv.port)
	if err != nil {
		log.WithError(err).Fatal("Couldn't resolve address")
	}
	listener, err := net.ListenTCP("tcp", tcpAddr)
	if err != nil {
		log.WithError(err).Fatal("Couldn't initiate TCP listening")
	}

	// creates a server
	config := &network.ServerCfg{
		MaxOutgoingChannels: MAX_OUT_CHANNELS,
		MaxIncomingChannels: MAX_IN_CHANNELS,
	}
	srv.server = *network.NewServer(config, srv, &packetReader{})

	if srv.telnet != nil {
		// start telnet server if present
		srv.telnet.Start(srv.gameWaitGroup)
		registerTelnetCommands(srv.telnet, &srv.clients)
	}

	srv.gameWaitGroup.Add(1)

	// starts the server in a listening goroutine
	go srv.server.Start(listener, time.Second)
	log.WithField("addr", listener.Addr()).Info("Server ready, listening for incoming connections")
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
	msg := packet.(*messages.Message)

	log.WithFields(log.Fields{
		"clientData": clientData,
		"addr":       c.GetRawConn().RemoteAddr(),
		"msg":        msg,
	}).Debug("Incoming message")

	switch msg.Type {
	case messages.PingId:
		// ping requires an immediate pong reply
		if err := srv.handlePing(c, msg); err != nil {
			log.WithError(err).Error("Couldn't handle Ping")
			return false
		}
	case messages.JoinId:
		if err := srv.handleJoin(c, msg); err != nil {
			log.WithError(err).Error("Couldn't handle Join")
			return false
		}
	default:
		// forward it
		srv.msgcb(msg, clientData.Id)
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
		msg := messages.NewMessage(messages.LeaveId,
			messages.LeaveMsg{
				Id:     uint32(clientData.Id),
				Reason: "client disconnection",
			})
		srv.Broadcast(msg)
	} else {
		// the client was not marked as JOINED, so nobody knows about him
		// and we have nothing more to do
	}
	// send a LEAVE to the game loop (server-only msg)
	srv.msgcb(messages.NewMessage(messages.LeaveId, messages.LeaveMsg{}), clientData.Id)
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
	srv.gameWaitGroup.Done()
}
