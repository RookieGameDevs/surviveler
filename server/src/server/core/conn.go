package core

import (
	"errors"
	"net"
	"sync"
	"sync/atomic"
	"time"
)

// Error types
var (
	ErrClosedConnection = errors.New("connection already closed")
	ErrBlockingWrite    = errors.New("blocking tcp write")
	ErrBlockingRead     = errors.New("blocking tcp read")
)

// Conn is an opaque structure, holding the underlying TCP connection, the
// message channels and the logic for resources cleanup and synchronization
type Conn struct {
	srv          *Server
	conn         *net.TCPConn  // underlying tcp connection
	closeOnce    sync.Once     // close the conn, once, per instance
	closeFlag    int32         // close flag
	closeChan    chan struct{} // close chanel
	outgoingChan chan Message  // chanel sending outgoing messages
	incomingChan chan Message  // chanel receiving incoming messages
}

// ConnEvtHandler is the interface that handles connection events
type ConnEvtHandler interface {
	// OnConnect is called once per connection. A false return value indicates
	// the connection should be closed.
	OnConnect(*Conn) bool

	// OnMessage is called when an incoming message has been received.
	// A false return value indicates the connection should be closed.
	OnIncomingMsg(*Conn, Message) bool

	// OnClose is called when the connection has been closed
	OnClose(*Conn)
}

// newConn returns a new Conn instance
func newConn(conn *net.TCPConn, srv *Server) *Conn {
	return &Conn{
		srv:          srv,
		conn:         conn,
		closeChan:    make(chan struct{}),
		outgoingChan: make(chan Message, srv.config.MaxOutgoingChannels),
		incomingChan: make(chan Message, srv.config.MaxIncomingChannels),
	}
}

// GetRawConn returns the underlying net.TCPConn from the Conn
func (c *Conn) GetRawConn() *net.TCPConn {
	return c.conn
}

// Close closes the connection
func (c *Conn) Close() {
	c.closeOnce.Do(func() {
		atomic.StoreInt32(&c.closeFlag, 1)
		close(c.closeChan)
		close(c.outgoingChan)
		close(c.incomingChan)
		c.conn.Close()
		c.srv.callback.OnClose(c)
	})
}

// IsClosed indicates whether or not the connection is closed
func (c *Conn) IsClosed() bool {
	return atomic.LoadInt32(&c.closeFlag) == 1
}

// AsyncSendMessage sends a message (guaranteed unblocking, or return error)
func (c *Conn) AsyncSendMessage(msg Message, timeout time.Duration) (err error) {
	if c.IsClosed() {
		return ErrClosedConnection
	}

	defer func() {
		if e := recover(); e != nil {
			err = ErrClosedConnection
		}
	}()

	if timeout == 0 {
		select {
		case c.outgoingChan <- msg:
			return nil

		default:
			return ErrBlockingWrite
		}

	} else {
		select {
		case c.outgoingChan <- msg:
			return nil

		case <-c.closeChan:
			return ErrClosedConnection

		case <-time.After(timeout):
			return ErrBlockingWrite
		}
	}
}

// StartLoops starts the various goroutines for current connection
func (c *Conn) StartLoops() {
	if !c.srv.callback.OnConnect(c) {
		return
	}

	// starts event handling goroutine
	c.srv.waitGroup.Add(1)
	go func() {
		c.handleLoop()
		c.srv.waitGroup.Done()
	}()

	// starts read goroutine
	c.srv.waitGroup.Add(1)
	go func() {
		c.readLoop()
		c.srv.waitGroup.Done()
	}()

	// starts write goroutine
	c.srv.waitGroup.Add(1)
	go func() {
		c.writeLoop()
		c.srv.waitGroup.Done()
	}()
}

// readLoop loops forever and reads incoming message from the client, while
// handling server exit and connection closing
func (c *Conn) readLoop() {
	defer func() {
		recover()
		c.Close()
	}()

	for {
		select {
		case <-c.srv.exitChan:
			return

		case <-c.closeChan:
			return

		default:
		}

		// Read and decode incoming message
		msg, err := c.srv.msgReader.ReadMessage(c.conn)
		if err != nil {
			return
		}

		// send the received message for further processing
		c.incomingChan <- msg
	}
}

// writeLoop loops forever and writes outgoing packet to the client, while
// handling server exit and connection closing
func (c *Conn) writeLoop() {
	defer func() {
		recover()
		c.Close()
	}()

	for {
		select {
		case <-c.srv.exitChan:
			return

		case <-c.closeChan:
			return

		case msg := <-c.outgoingChan:
			if c.IsClosed() {
				return
			}
			if _, err := c.conn.Write(msg.Serialize()); err != nil {
				return
			}
		}
	}
}

// handleLoop loops forever and handles connection/server specific events
func (c *Conn) handleLoop() {
	defer func() {
		recover()
		c.Close()
	}()

	for {
		select {
		case <-c.srv.exitChan:
			return

		case <-c.closeChan:
			return

		case msg := <-c.incomingChan:
			if c.IsClosed() {
				return
			}
			// invoke the provided callback with the decoded incoming msg
			if !c.srv.callback.OnIncomingMsg(c, msg) {
				return
			}
		}
	}
}
