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

func (g *Game) OnIncomingMsg(c *network.Conn, cm network.Message) bool {

	client := g.clients.getClient(c)
	fmt.Printf("Received message from client, id %v addr %v\n",
		client.Id, c.GetRawConn().RemoteAddr())

	var msg *Message
	var ok bool
	if msg, ok = cm.(*Message); !ok {
		panic("type assertion")
	}

	switch msg.Type {
	case PingId:

		// handle ping

		// temporary: for now we do it here... but it will be handled in
		// registered handlers using observers/notifiers...
		fmt.Printf("Received Ping: %v\n", msg)
		iping, err := g.msgFactory.DecodePayload(PingId, msg.Buffer)

		var ping PingMsg
		var ok bool
		if ping, ok = iping.(PingMsg); !ok {
			panic("type assertion")
		}
		fmt.Printf("Decoded Ping: %v\n", ping)

		// reply pong
		pong, err := NewMessage(MsgType(PongId), PongMsg{ping.Id, MakeTimestamp()})
		err = c.AsyncSendMessage(pong, time.Second)
		if err != nil {
			fmt.Printf("Error in AsyncSendMessage: %v\n", err)
			return false
		}
		fmt.Println("Sent a Pong")

	default:
		fmt.Printf("Unknown MsgType: %v\n", msg)
		return false
	}

	return true
}

func (g *Game) OnClose(c *network.Conn) {
	fmt.Printf("Connection closed: %v\n", c.GetRawConn().RemoteAddr())
}
