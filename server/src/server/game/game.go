package game

import (
	log "github.com/Sirupsen/logrus"
	"os"
	"os/signal"
	"runtime"
	"server/network"
	"syscall"
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
	Port  string
	Debug bool
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

	// setup logger
	if g.cfg.Debug {
		log.StandardLogger().Level = log.DebugLevel
	}

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

	log.Info("Starting Surviveler server")
	g.startServer()
	//g.loop()

	// be notified of termination signals
	chSig := make(chan os.Signal)
	signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)

	// wait for termination signals
	log.WithField("signal", <-chSig).Info("Received termination signal")
	g.Stop()
}

/*
 * Stop cleanups the server and exists the various loops
 */
func (g *Game) Stop() {
	// stop ticking
	log.Info("Stopping game heartbeat")
	g.ticker.Stop()

	// stop server
	log.Info("Stopping server")
	g.server.Stop()
}
