package game

import (
	"fmt"
	"runtime"
	"server/network"
	"time"
)

const (
	MAX_OUT_CHANNELS = 100
	MAX_IN_CHANNELS  = 100
)

/*
 * GameCfg contains all the configurable server-specific game settings
 */
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
	ticker     time.Ticker    // our tick source
}

/*
 *Setup initializes the different game subsystems
 */
func (g *Game) Setup(cfg GameCfg) {
	g.cfg = cfg

	// setup go runtime
	runtime.GOMAXPROCS(runtime.NumCPU())

	// register the message types
	g.msgFactory = *NewMsgFactory()
	g.msgFactory.RegisterMsgTypes()

	// setup client registry
	g.clients.Init()

	// set up the game ticker
	g.ticker = *time.NewTicker(time.Millisecond * 100)
}

/*
 * Start starts the server and game loops
 */
func (g *Game) Start() {
	g.startServer()
	g.loop()
}

/*
 * Stop kicks all clients and stops the various loops
 */
func (g *Game) Stop() {
	// stop ticking
	fmt.Println("Stop heartbeat")
	g.ticker.Stop()

	// kick the clients
	fmt.Println("Kick clients")
	g.clients.kick()

	// stop server
	fmt.Println("Stop server")
	g.server.Stop()
}
