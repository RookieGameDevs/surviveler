package game

import (
	log "github.com/Sirupsen/logrus"
	"net"
	"server/network"
	"time"
)

/*
 * startServer creates the TCP server and starts the listening goroutine
 */
func (g *Game) startServer() {
	// creates a tcp listener
	tcpAddr, err := net.ResolveTCPAddr("tcp4", ":"+g.cfg.Port)
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
	g.server = *network.NewServer(config, g, &MsgReader{})

	// starts the server in a listening goroutine
	go g.server.Start(listener, time.Second)
	log.WithField("addr", listener.Addr()).Info("Server ready , starting to listen")
}

/*
 * OnConnect gets called by the server at connection initialization, once by
 * connection. This gives us the chance to register a new client and perform
 * the client initialization
 */
func (g *Game) OnConnect(c *network.Conn) bool {
	// register our new client
	g.clients.registerClient(c)

	// start a goroutine that spams client with player position!
	go func() {

		for {
			switch {
			case c.IsClosed():
				return
			default:

				// temporary: for now spam a position every 200ms
				msg, err := NewMessage(MsgType(PositionId), PositionMsg{10, 15})

				err = c.AsyncSendMessage(msg, time.Second)
				if err != nil {
					log.WithError(err).Error("Couldn't send async message")
					return
				}
				log.Debug("Sent a PositionMsg")
				time.Sleep(200 * time.Millisecond)
			}
		}
	}()

	return true
}

/*
 * OnIncomingMsg gets called by the server each time a message is ready to be
 * read on the connection
 */
func (g *Game) OnIncomingMsg(c *network.Conn, netmsg network.Message) bool {
	clientId := g.clients.getClientId(c)
	log.WithFields(log.Fields{
		"id":   clientId,
		"addr": c.GetRawConn().RemoteAddr(),
	}).Debug("Received message")

	msg := netmsg.(*Message)
	if msg.Type == PingId {
		// ping requires an immediate pong reply
		if err := g.handlePing(c, msg); err != nil {
			log.WithError(err).Error("Couldn't handle ping")
			return false
		}
	}
	return true
}

/*
 * handlePing processes the PingMsg as it needs an immediate PongMsg response
 */
func (g *Game) handlePing(c *network.Conn, msg *Message) error {
	// decode ping msg payload into an interface
	iping, err := g.msgFactory.DecodePayload(PingId, msg.Buffer)
	if err != nil {
		return err
	}

	ping := iping.(PingMsg)
	log.WithField("msg", ping).Debug("Received ping")

	// reply pong
	pong, err := NewMessage(MsgType(PongId), PongMsg{ping.Id, MakeTimestamp()})
	err = c.AsyncSendMessage(pong, time.Second)
	if err != nil {
		return err
	}
	log.WithField("msg", ping).Debug("Sent pong")
	return nil
}

/*
 * OnClose gets called by the server at connection closing, once by
 * connection. This gives us the chance to unregister a new client and perform
 * client cleanup
 */
func (g *Game) OnClose(c *network.Conn) {
	log.WithField("addr", c.GetRawConn().RemoteAddr()).Debug("Connection closed")
}
