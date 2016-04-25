package game

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"net"
	"os"
	"os/signal"
	"runtime"
	"server/core"
	"syscall"
	"time"

	"github.com/ugorji/go/codec"
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

		var mh codec.MsgpackHandle

		var msg OutgoingMsg

		// create a buffer to contain a (X,Y) position: 2 x uint16 position: 4 Bytes
		type Pos struct{ Xpos, Ypos uint16 }
		pos := Pos{10, 15}

		for {
			switch {
			case c.IsClosed():
				return
			default:

				var err error
				t := time.Now()
				msg.Timestamp = t.Unix()

				// Encode to msgpack
				bb := new(bytes.Buffer)
				var enc *codec.Encoder = codec.NewEncoder(bb, &mh)
				err = enc.Encode(pos)
				if err != nil {
					fmt.Printf("Error encoding pos: %v\n", err)
					return
				}

				// Encode to network byte order
				bbuf := bytes.NewBuffer(make([]byte, 0, len(bb.Bytes())))
				binary.Write(bbuf, binary.BigEndian, bb.Bytes())

				// Copy the buffer
				msg.Buffer = bbuf.Bytes()

				// Length is the buffer length + timestamp length
				msg.Length = uint16(len(msg.Buffer) + 8)

				err = c.AsyncSendMessage(msg, time.Second)
				if err != nil {
					fmt.Printf("Error in AsyncSendMessage: %v\n", err)
					return
				}
				fmt.Println("Sent msg in AsyncSendMessage")
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
