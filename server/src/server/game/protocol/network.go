package protocol

import (
	log "github.com/Sirupsen/logrus"
	"net"
	"server/network"
	"time"
)

const (
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

type ClientMessageHandler func(*Message, uint16)

/*
 * Server represents a TCP server. It implements the Broadcaster and
 * network.ConnEvtHandler interfaces.
 */
type Server struct {
	port       string
	server     network.Server // tcp server instance
	msgFactory MsgFactory
	clients    ClientRegistry // manage the connected clients
	handler    ClientMessageHandler
}

/*
 * NewServer returns a new configured Server instance
 */
func NewServer(port string, h ClientMessageHandler) *Server {

	srv := new(Server)
	srv.port = port
	srv.handler = h

	// register the message types
	srv.msgFactory = NewMsgFactory()
	srv.msgFactory.RegisterMsgTypes()

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
	clientId := srv.clients.register(c)

	// send a AddPlayerMsg to the game loop (server-only msg)
	if msg, err := NewMessage(MsgType(AddPlayerId), AddPlayerMsg{"batman"}); err == nil {
		srv.handler(msg, clientId)
	} else {
		log.WithError(err).Fatal("Couldn't create AddPlayerMsg")
	}

	return true
}

/*
 * OnIncomingMsg gets called by the server each time a message is ready to be
 * read on the connection
 */
func (srv *Server) OnIncomingMsg(c *network.Conn, netmsg network.Message) bool {
	clientId := c.GetUserData().(uint16)
	log.WithFields(log.Fields{
		"id":   clientId,
		"addr": c.GetRawConn().RemoteAddr(),
	}).Debug("Received message")

	msg := netmsg.(*Message)
	if msg.Type == PingId {
		// ping requires an immediate pong reply
		if err := srv.handlePing(c, msg); err != nil {
			log.WithError(err).Error("Couldn't handle ping")
			return false
		}
	}
	return true
}

/*
 * handlePing processes a PingMsg and immediately replies with a PongMsg
 */
func (srv *Server) handlePing(c *network.Conn, msg *Message) error {
	// decode ping msg payload into an interface
	var ping PingMsg
	if iping, err := srv.msgFactory.DecodePayload(PingId, msg.Buffer); err != nil {
		return err
	} else {
		ping = iping.(PingMsg)
	}

	log.WithField("msg", ping).Debug("Received ping")

	// reply pong
	ts := time.Now().UnixNano() / int64(time.Millisecond)
	pong, err := NewMessage(MsgType(PongId), PongMsg{ping.Id, ts})
	if err = c.AsyncSendMessage(pong, time.Second); err != nil {
		return err
	}
	log.WithField("msg", pong).Debug("Sent pong")
	return nil
}

/*
 * OnClose gets called by the server at connection closing, once by
 * connection. This gives us the chance to unregister a new client and perform
 * client cleanup
 */
func (srv *Server) OnClose(c *network.Conn) {

	clientId := c.GetUserData().(uint16)
	log.WithField("addr", c.GetRawConn().RemoteAddr()).Debug("Connection closed")

	// send a DelPlayerMsg to the game loop (server-only msg)
	if msg, err := NewMessage(MsgType(DelPlayerId), DelPlayerMsg{}); err == nil {
		srv.handler(msg, clientId)
	} else {
		log.WithError(err).Fatal("Couldn't create DelPlayerMsg")
	}
}

/*
 * Broadcast sends a message to all clients
 */
func (srv *Server) Broadcast(msg *Message) error {

	// protect client map access (read)
	return srv.clients.Broadcast(msg)
}

/*
 * Stop stops the tcp server and the clients connections
 */
func (srv *Server) Stop() {
	log.Info("Stopping server")
	srv.server.Stop()
}
