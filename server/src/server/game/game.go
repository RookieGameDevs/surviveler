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
	"server/game/messages"
	"server/game/protocol"
	"syscall"
	"time"
)

/*
 * Game is the main game structure. It also implements the
 * network.ConnEvtHandler interface
 */
type Game struct {
	cfg           Config                      // configuration settings
	server        protocol.Server             // server core
	ticker        time.Ticker                 // our tick source
	msgChan       chan messages.ClientMessage // conducts ClientMessage to the game loop
	loopCloseChan chan struct{}               // signal the game loop it must end
	telnet        *protocol.TelnetServer      // if enabled, the telnet server
}

/*
 * Setup initializes the different game subsystems
 */
func (g *Game) Setup() {

	// get configuration
	g.cfg = ParseConfig()

	// setup logger
	log.StandardLogger().Level = g.cfg.LogLevel

	// dump config
	log.WithField("cfg", g.cfg).Info("Game configuration")

	// setup go runtime
	runtime.GOMAXPROCS(runtime.NumCPU())

	// init channels
	g.msgChan = make(chan messages.ClientMessage)
	g.loopCloseChan = make(chan struct{})

	// creates the client registry
	registry := protocol.NewClientRegistry()

	// setup a telnet server
	if len(g.cfg.TelnetPort) > 0 {
		g.telnet = protocol.NewTelnetServer(g.cfg.TelnetPort, registry)
	}

	// setup TCP server
	rootHandler := func(msg *messages.Message, clientId uint32) error {
		// forward incoming messages to the game loop
		g.msgChan <- messages.ClientMessage{msg, clientId}
		return nil
	}
	g.server = *protocol.NewServer(g.cfg.Port, rootHandler, registry, g.telnet)
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
	log.WithField("signal", <-chSig).Warn("Received termination signal")

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
