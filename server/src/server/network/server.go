/*
	Server
*/
package network

import (
	"net"
	"sync"
	"time"
)

type ServerCfg struct {
	MaxOutgoingChannels uint32 // maximum number of send channels
	MaxIncomingChannels uint32 // maximum bumber of receive channels
}

type Server struct {
	config    *ServerCfg      // server configuration
	callback  ConnEvtHandler  // message callbacks in connection
	msgReader MessageReader   // customized message reader
	exitChan  chan struct{}   // notify all goroutines to shutdown
	waitGroup *sync.WaitGroup // wait for all goroutines
}

// NewServer creates a server
func NewServer(cfg *ServerCfg, callback ConnEvtHandler, msgReader MessageReader) *Server {
	return &Server{
		config:    cfg,
		callback:  callback,
		msgReader: msgReader,
		exitChan:  make(chan struct{}),
		waitGroup: &sync.WaitGroup{},
	}
}

// Start runs the server main listening loop
func (s *Server) Start(listener *net.TCPListener, acceptTimeout time.Duration) {
	s.waitGroup.Add(1)
	defer func() {
		listener.Close()
		s.waitGroup.Done()
	}()

	for {
		select {
		case <-s.exitChan:
			return

		default:
		}

		listener.SetDeadline(time.Now().Add(acceptTimeout))

		conn, err := listener.AcceptTCP()
		if err != nil {
			continue
		}

		s.waitGroup.Add(1)
		go func() {
			newConn(conn, s).StartLoops()
			s.waitGroup.Done()
		}()
	}
}

// Stop exits the server gracefully
func (s *Server) Stop() {
	close(s.exitChan)
	s.waitGroup.Wait()
}
