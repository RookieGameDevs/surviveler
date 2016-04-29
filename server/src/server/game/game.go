package game

import (
	"fmt"
	"runtime"
	"server/network"
)

const (
	CONN_HOST        = ""
	CONN_PORT        = "1234"
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

type GameCfg struct {
	Port string
}

/*
 * Game is the main game structure. It also implements the
 * network.ConnEvtHandler interface
 */
type Game struct {
	cfg        GameCfg        // configuration settings
	msgFactory MsgFactory     // message factory
	server     network.Server // tcp server instance
	clients    ClientRegistry // manage the connected clients
}

// Setup initializes the different game subsystems
func (g *Game) Setup(cfg GameCfg) {
	g.cfg = cfg

	// setup go runtime
	runtime.GOMAXPROCS(runtime.NumCPU())

	// register the client-server message types
	g.registerMsgTypes()

	// setup client registry
	g.clients.Init()
}

// Start starts the server and game loops
func (g *Game) Start() {
	g.startServer()
}

// Stop stops kicks all clients and stop the various loops
func (g *Game) Stop() {
	fmt.Println("Stopping the game...")

	// TODO: kick the clients

	// stops server
	g.server.Stop()
}

func (g *Game) registerMsgTypes() {
	// creates the factory and register message types
	g.msgFactory = *NewMsgFactory()
	g.msgFactory.RegisterMsgType(PingId, PingMsg{})
	g.msgFactory.RegisterMsgType(PongId, PongMsg{})
	g.msgFactory.RegisterMsgType(PositionId, PositionMsg{})
}
