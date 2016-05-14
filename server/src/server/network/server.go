/*
 * Generic network package
 * server implementation
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
	callback  ConnEvtHandler  // packet callbacks in connection
	msgReader PacketReader    // customized packet reader
	exitChan  chan struct{}   // notify all goroutines to shutdown
	waitGroup *sync.WaitGroup // wait for all goroutines
}

/*
 * NewServer creates a server
 */
func NewServer(cfg *ServerCfg, callback ConnEvtHandler, msgReader PacketReader) *Server {
	return &Server{
		config:    cfg,
		callback:  callback,
		msgReader: msgReader,
		exitChan:  make(chan struct{}),
		waitGroup: &sync.WaitGroup{},
	}
}

/*
 * Start runs the server main listening loop
 */
func (s *Server) Start(listener *net.TCPListener, acceptTimeout time.Duration) {
	// we want to close the listener when we'll be quitting
	s.waitGroup.Add(1)
	defer func() {
		listener.Close()
		s.waitGroup.Done()
	}()

	for {
		// loop forever...
		select {
		case <-s.exitChan:
			// ...until the server quits
			return

		default:
		}

		// listening for incoming TCP connections
		listener.SetDeadline(time.Now().Add(acceptTimeout))
		conn, err := listener.AcceptTCP()
		if err != nil {
			// wrong connection, leave it
			continue
		}

		// start a new goroutine, one more to wait for when we'll be quitting
		s.waitGroup.Add(1)
		go func() {
			// disable Nagle algorithm
			conn.SetNoDelay(true)
			newConn(conn, s).StartLoops()
			s.waitGroup.Done()
		}()
	}
}

/*
 * Stop exits the server gracefully
 */
func (s *Server) Stop() {
	// signal every goroutine that we are quitting
	close(s.exitChan)
	// ...and wait for them to finish
	s.waitGroup.Wait()
}
