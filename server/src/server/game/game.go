/*
 * Surviveler game package
 * game entry & exit points
 */
package game

import (
	log "github.com/Sirupsen/logrus"
	"os"
	"os/signal"
	"runtime"
	"server/game/protocol"
	"syscall"
	"time"
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
	cfg           GameCfg                     // configuration settings
	server        protocol.Server             // server core
	ticker        time.Ticker                 // our tick source
	msgChan       chan protocol.ClientMessage // conducts ClientMessage to the game loop
	loopCloseChan chan struct{}               // indicates to the game loop that it may exit
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

	// init channels
	g.msgChan = make(chan protocol.ClientMessage)
	g.loopCloseChan = make(chan struct{})

	// setup server
	msgHandler := func(msg protocol.Message, clientId uint16) error {
		// forward incoming messages to the game loop
		g.msgChan <- protocol.ClientMessage{&msg, clientId}
		return nil
	}
	g.server = *protocol.NewServer(g.cfg.Port, msgHandler)
}

/*
 * Start starts the server and game loops
 */
func (g *Game) Start() {

	log.Info("Starting Surviveler server")

	// start everything
	g.server.Start()
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
	g.server.Stop()

	// stop game loop
	log.Info("Stopping game loop")
	g.loopCloseChan <- struct{}{}
	defer close(g.loopCloseChan)
}
