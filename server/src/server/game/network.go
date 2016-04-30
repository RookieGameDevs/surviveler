package game

import (
	"fmt"
	"net"
	"server/network"
	"time"
)

func (g *Game) startServer() {
	// creates a tcp listener
	tcpAddr, err := net.ResolveTCPAddr("tcp4", ":"+g.cfg.Port)
	FatalError(err, "Resolving addr")
	listener, err := net.ListenTCP("tcp", tcpAddr)
	FatalError(err, "Listening TCP")

	// creates a server
	config := &network.ServerCfg{
		MaxOutgoingChannels: MAX_OUT_CHANNELS,
		MaxIncomingChannels: MAX_IN_CHANNELS,
	}
	g.server = *network.NewServer(config, g, &MsgReader{})

	// starts the server in a listening goroutine
	go g.server.Start(listener, time.Second)
	fmt.Println("Server is ready, listening at:", listener.Addr())
}

// OnConnect is called at connection initialization, once by connection
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
					fmt.Printf("Error in AsyncSendMessage: %v\n", err)
					return
				}
				fmt.Println("Sent a PositionMsg")
				time.Sleep(200 * time.Millisecond)
			}
		}
	}()

	return true
}

func (g *Game) OnIncomingMsg(c *network.Conn, netmsg network.Message) bool {
	clientId := g.clients.getClientId(c)
	fmt.Printf("Received message from client, id %v addr %v\n",
		clientId, c.GetRawConn().RemoteAddr())

	msg := netmsg.(*Message)

	if msg.Type == PingId {
		// ping requires an immediate pong reply
		if err := g.handlePing(c, msg); err != nil {
			fmt.Printf("Error calling handlePing: %v\n", err)
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
	fmt.Printf("Received Ping: %v\n", ping)

	// reply pong
	pong, err := NewMessage(MsgType(PongId), PongMsg{ping.Id, MakeTimestamp()})
	err = c.AsyncSendMessage(pong, time.Second)
	if err != nil {
		return err
	}
	fmt.Println("Sent a Pong")
	return nil
}

func (g *Game) OnClose(c *network.Conn) {
	fmt.Printf("Connection closed: %v\n", c.GetRawConn().RemoteAddr())
}
