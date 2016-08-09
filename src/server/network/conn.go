/*
 * Generic network package
 * TCP connection
 */
package network

import (
	"errors"
	"net"
	"sync"
	"sync/atomic"
	"time"

	log "github.com/Sirupsen/logrus"
)

/*
 * Error types
 */
var (
	ErrClosedConnection = errors.New("connection already closed")
	ErrBlockingWrite    = errors.New("blocking tcp write")
	ErrBlockingRead     = errors.New("blocking tcp read")
)

/*
 * Conn is an opaque structure, holding the underlying TCP connection, the
 * packet channels and the logic for resources cleanup and synchronization
 */
type Conn struct {
	srv          *Server
	conn         *net.TCPConn  // underlying tcp connection
	userData     interface{}   // associated user data
	closeOnce    sync.Once     // close the connection, once, per instance
	closeFlag    int32         // close flag
	closeChan    chan struct{} // close chanel
	outgoingChan chan Packet   // chanel sending outgoing packets
	incomingChan chan Packet   // chanel receiving incoming packets
}

/*
 * GetUserData retrieves the associated user data
 */
func (c *Conn) GetUserData() interface{} {
	return c.userData
}

/*
 * SetUserData associates user data with the connection
 */
func (c *Conn) SetUserData(data interface{}) {
	// TODO: protect again more than one call, using sync.Once
	c.userData = data
}

/*
 * ConnEvtHandler is the interface that handles connection events
 */
type ConnEvtHandler interface {
	// OnConnect is called once per connection. A false return value indicates
	// the connection should be closed.
	OnConnect(*Conn) bool

	// OnIncomingPacket is called when an incoming packet has been received.
	// A false return value indicates the connection should be closed.
	OnIncomingPacket(*Conn, Packet) bool

	// OnClose is called when the connection has been closed, once per connection.
	OnClose(*Conn)
}

/*
 * newConn returns a new Conn instance
 */
func newConn(conn *net.TCPConn, srv *Server) *Conn {
	return &Conn{
		srv:          srv,
		conn:         conn,
		closeChan:    make(chan struct{}),
		outgoingChan: make(chan Packet, srv.config.MaxOutgoingChannels),
		incomingChan: make(chan Packet, srv.config.MaxIncomingChannels),
	}
}

/*
 * GetRawConn returns the underlying net.TCPConn from the Conn
 */
func (c *Conn) GetRawConn() *net.TCPConn {
	return c.conn
}

/*
 * Close closes the connection
 */
func (c *Conn) Close() {
	c.closeOnce.Do(func() {
		// atomically set to 1, so concurrent accesses always have the latest value
		atomic.StoreInt32(&c.closeFlag, 1)

		// close all the channels
		close(c.closeChan)
		close(c.outgoingChan)
		close(c.incomingChan)

		// close the underlying TCP connection
		c.conn.Close()

		// finally raise the callback
		c.srv.callback.OnClose(c)
	})
}

/*
 * IsClosed indicates whether a the connection is closed or not
 */
func (c *Conn) IsClosed() bool {
	// again, atomatically read it, so that concurrent accesses always have the latest value
	return atomic.LoadInt32(&c.closeFlag) == 1
}

/*
 * AsyncSendPacket sends a packet (guaranteed unblocking, or return error)
 */
func (c *Conn) AsyncSendPacket(msg Packet, timeout time.Duration) (err error) {
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
			// in case of no timeout, raise an error if we couldn't send immediately
			return ErrBlockingWrite
		}

	}

	select {
	case c.outgoingChan <- msg:
		return nil

	case <-c.closeChan:
		//  tried to send on a closed connection
		return ErrClosedConnection

	case <-time.After(timeout):
		// in case a timeout, raise an error once it has elapsed
		return ErrBlockingWrite
	}
}

/*
 * StartLoops starts the various goroutines for current connection
 */
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

/*
 * readLoop loops forever and reads incoming packet from the client, while
 * handling server exit and connection closing
 */
func (c *Conn) readLoop() {
	defer func() {
		recover()
		c.Close()
	}()

	for {
		select {
		// handle server exit
		case <-c.srv.exitChan:
			return

		// handle connection close
		case <-c.closeChan:
			return

		default:
		}

		// Read from the connection byte stream and unserialize into a packet
		msg, err := c.srv.msgReader.ReadPacket(c.conn)
		if err != nil {
			log.WithError(err).Warning("Error while reading packet")
			return
		}

		// send the received packet for further processing
		c.incomingChan <- msg
	}
}

/*
 * writeLoop loops forever and writes outgoing packet to the client, while
 * handling server exit and connection closing
 */
func (c *Conn) writeLoop() {
	defer func() {
		recover()
		c.Close()
	}()

	for {
		select {
		// handle server exit
		case <-c.srv.exitChan:
			return

		// handle connection close
		case <-c.closeChan:
			return

		// handle an outgoing packet
		case msg := <-c.outgoingChan:
			if c.IsClosed() {
				return
			}
			// write the serialized packet on the underlying TCP connection
			if _, err := c.conn.Write(msg.Serialize()); err != nil {
				return
			}
		}
	}
}

/*
 * handleLoop loops forever and handles connection/server specific events
 */
func (c *Conn) handleLoop() {
	defer func() {
		recover()
		c.Close()
	}()

	for {
		select {
		// handle server exit
		case <-c.srv.exitChan:
			return

		// handle connection close
		case <-c.closeChan:
			return

		// handle incoming packet
		case msg := <-c.incomingChan:
			if c.IsClosed() {
				return
			}
			// invoke the provided callback with the decoded incoming msg
			if !c.srv.callback.OnIncomingPacket(c, msg) {
				return
			}
		}
	}
}
