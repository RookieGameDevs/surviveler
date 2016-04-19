package game

import (
	"bitbucket.com/rookiegamedevs/surviveler/server/core"
	"fmt"
	"net"
	"os"
	"os/signal"
	"runtime"
	"syscall"
	"time"
)

const (
	CONN_HOST        = ""
	CONN_PORT        = "3333"
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
	srv := core.NewServer(config, &SurvCallback{})

	// starts service
	go srv.Start(listener, time.Second)
	fmt.Println("listening:", listener.Addr())

	// catchs system signal
	chSig := make(chan os.Signal)
	signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)
	fmt.Println("Signal: ", <-chSig)

	// stops service
	srv.Stop()
}

type SurvCallback struct {
}

func (this *SurvCallback) OnConnect(c *core.Conn) bool {
	addr := c.GetRawConn().RemoteAddr()
	fmt.Println("OnConnect:", addr)
	return true
}

func (this *SurvCallback) OnIncomingMsg(c *core.Conn, p core.IncomingMsg) bool {
	fmt.Println("OnIncomingMsg")
	return true
}

func (this *SurvCallback) OnClose(c *core.Conn) {
	fmt.Printf("OnClose(), conn.IsClosed() = %v\n", c.IsClosed())
}
