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
	cfg           GameCfg        // configuration settings
	msgFactory    MsgFactory     // message factory
	server        network.Server // tcp server instance
	clients       ClientRegistry // manage the connected clients
	ticker        time.Ticker    // our tick source
	msgChan       chan Message   // conducts the Message to the game loop
	loopCloseChan chan struct{}  // indicates to the game loop that it may exit
}

/*
 * Setup initializes the different game subsystems
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

	// init channels
	g.msgChan = make(chan Message)
	g.loopCloseChan = make(chan struct{})
}

/*
 * Start starts the server and game loops
 */
func (g *Game) Start() {

	log.Info("Starting Surviveler server")

	// start everything
	g.startServer()
	g.loop()

	// be notified of termination signals
	chSig := make(chan os.Signal)
	defer close(chSig)
	signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)
	log.WithField("signal", <-chSig).Info("Received termination signal")

	g.stop()
}

/*
 * stop cleanups the server and exits the various loops
 */
func (g *Game) stop() {
	// stop game loop
	log.Info("Stopping game loop")
	g.loopCloseChan <- struct{}{}

	// stop server
	log.Info("Stopping server")
	g.server.Stop()
}
