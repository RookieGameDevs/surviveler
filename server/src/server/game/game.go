package game

import (
	"fmt"
	"net"
	"os"
	"os/signal"
	"runtime"
	"server/core"
	"syscall"
	"time"
)

const (
	CONN_HOST        = ""
	CONN_PORT        = "1234"
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

func StartGameServer() {
	runtime.GOMAXPROCS(runtime.NumCPU())

	// creates a tcp listener
	tcpAddr, err := net.ResolveTCPAddr("tcp4", CONN_HOST+":"+CONN_PORT)
	FatalError(err, "Resolving addr")
	listener, err := net.ListenTCP("tcp", tcpAddr)
	FatalError(err, "Listening TCP")

	// creates a server
	config := &core.ServerCfg{
		MaxOutgoingChannels: MAX_OUT_CHANNELS,
		MaxIncomingChannels: MAX_IN_CHANNELS,
	}
	srv := core.NewServer(config, &SurvCallback{}, &IncomingMsgReader{})

	// starts server (listening goroutine)
	go srv.Start(listener, time.Second)
	fmt.Println("listening:", listener.Addr())

	// catchs system signal
	chSig := make(chan os.Signal)
	signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)
	fmt.Println("Signal: ", <-chSig)

	// stops server
	srv.Stop()
}

type SurvCallback struct {
	Addr net.Addr
}

func (this *SurvCallback) OnConnect(c *core.Conn) bool {

	this.Addr = c.GetRawConn().RemoteAddr()
	fmt.Println("OnConnect:", this.Addr)

	// start a goroutine that spams client with player position!
	go func() {

		for {
			switch {
			case c.IsClosed():
				return
			default:

				msg, err := NewOutgoingPosMsg(2, Pos{10, 15})

				err = c.AsyncSendMessage(msg, time.Second)
				if err != nil {
					fmt.Printf("Error in AsyncSendMessage: %v\n", err)
					return
				}
				fmt.Println("Sent a msg in AsyncSendMessage")
				time.Sleep(200 * time.Millisecond)
			}
		}
	}()

	return true
}

func (this *SurvCallback) OnIncomingMsg(c *core.Conn, msg core.Message) bool {
	fmt.Println("OnIncomingMsg")
	return true
}

func (this *SurvCallback) OnClose(c *core.Conn) {
	fmt.Printf("OnClose(), conn.IsClosed() = %v\n", c.IsClosed())
}
