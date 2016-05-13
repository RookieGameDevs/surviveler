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
	"time"
)

const (
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

/*
 * Broadcaster is the interface that wraps that Broadcast method. It implements
 * the Broadcaster interface.
 */
type Broadcaster interface {

	// Broadcast broadcasts a message.
	Broadcast(msg *Message) error
}

type MsgCallbackFunc func(msg *Message, clientId uint16) error

/*
 * Server represents a TCP server. It implements the Broadcaster and
 * network.ConnEvtHandler interfaces.
 */
type Server struct {
	port    string
	server  network.Server  // tcp server instance
	clients ClientRegistry  // manage the connected clients
	msgcb   MsgCallbackFunc // incoming messages callback
}

/*
 * NewServer returns a new configured Server instance
 */
func NewServer(port string, msgcb MsgCallbackFunc) *Server {

	srv := new(Server)
	srv.port = port
	srv.msgcb = msgcb

	return srv
}

/*
 * Start creates the TCP server and starts the listening goroutine
 */
func (srv *Server) Start() {

	// setup client registry
	srv.clients.init()

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
	srv.server = *network.NewServer(config, srv, &MsgReader{})

	// starts the server in a listening goroutine
	go srv.server.Start(listener, time.Second)
	log.WithField("addr", listener.Addr()).Info("Server ready , starting to listen")
}

/*
 * OnConnect gets called by the server at connection initialization, once by
 * connection. This gives us the chance to register a new client and perform
 * the client initialization
 */
func (srv *Server) OnConnect(c *network.Conn) bool {
	// register our new client
	srv.clients.register(c)
	return true
}

/*
 * OnIncomingMsg gets called by the server each time a message has been read
 * from the connection
 */
func (srv *Server) OnIncomingMsg(c *network.Conn, netmsg network.Message) bool {
	clientData := c.GetUserData().(ClientData)
	log.WithFields(log.Fields{
		"clientData": clientData,
		"addr":       c.GetRawConn().RemoteAddr(),
	}).Debug("Received message")

	msg := netmsg.(*Message)
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
	srv.clients.unregister(clientData.ClientId)

	if clientData.Joined {
		// client is still JOINED so that's a disconnection initiated externally
		// send a LEAVE to the rest of the world
		msg := NewMessage(messages.LeaveId, messages.LeaveMsg{
			Id:     uint32(clientData.ClientId),
			Reason: "client disconnection",
		})
		srv.Broadcast(msg)
	}
	// send a LEAVE to the game loop (server-only msg)
	srv.msgcb(NewMessage(messages.LeaveId, messages.LeaveMsg{}), clientData.ClientId)
}

/*
 * Broadcast sends a message to all clients
 */
func (srv *Server) Broadcast(msg *Message) error {
	return srv.clients.Broadcast(msg)
}

/*
 * Stop stops the tcp server and the clients connections
 */
func (srv *Server) Stop() {
	log.Info("Stopping server")
	srv.server.Stop()
}

/*
 * handlePing processes a PingMsg and immediately replies with a PongMsg
 */
func (srv *Server) handlePing(c *network.Conn, msg *Message) error {
	// decode ping msg payload into an interface
	var ping messages.PingMsg
	if iping, err := messages.GetFactory().DecodePayload(messages.PingId, msg.Buffer); err != nil {
		return err
	} else {
		ping = iping.(messages.PingMsg)
	}

	log.WithField("msg", ping).Debug("Received Ping")

	// reply pong
	ts := time.Now().UnixNano() / int64(time.Millisecond)
	pong := NewMessage(messages.PongId, messages.PongMsg{ping.Id, ts})
	if err := c.AsyncSendMessage(pong, time.Second); err != nil {
		return err
	}
	log.WithField("msg", pong).Debug("Sent Pong")
	return nil
}

func (srv *Server) handleJoin(c *network.Conn, msg *Message) error {
	clientData := c.GetUserData().(ClientData)
	log.Debug("Handling Join")

	if clientData.Joined {
		// TODO: handle this
		// protocol error: second JOIN received
		log.Warn("Second JOIN of same connection: not implemented!")
	} else {
		// decode join msg payload into an interface
		var join messages.JoinMsg
		if ijoin, err := messages.GetFactory().DecodePayload(messages.JoinId, msg.Buffer); err != nil {
			return err
		} else {
			join = ijoin.(messages.JoinMsg)
		}

		// check conditions
		accepted := true

		// accepted?
		if accepted {
			// send JOINED and STAY
			srv.Broadcast(NewMessage(messages.JoinedId, messages.JoinedMsg{
				Id:   uint32(clientData.ClientId),
				Name: clientData.Name,
			}))

			// informs the game loop that we have a new player
			srv.msgcb(NewMessage(messages.JoinId, join), clientData.ClientId)
		}
	}
	return nil
}
