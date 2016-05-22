/*
 * Surviveler game package
 * game entry & exit points
 */
package game

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"os"
	"os/signal"
	"runtime"
	"server/game/messages"
	"server/game/protocol"
	"server/game/resource"
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
	clients       *protocol.ClientRegistry    // the client registry
	telnet        *protocol.TelnetServer      // if enabled, the telnet server
	telnetChan    chan TelnetRequest          // channel for game related telnet commands
	assets        resource.SurvivelerPackage  // game assets package
	worldMap      Map                         // world map
}

/*
 * Setup initializes the different game subsystems
 */
func (g *Game) Setup() bool {
	// get configuration
	g.cfg = ParseConfig()

	// setup logger
	log.StandardLogger().Level = g.cfg.LogLevel

	// dump config
	log.WithField("cfg", g.cfg).Info("Game configuration")

	// setup go runtime
	runtime.GOMAXPROCS(runtime.NumCPU())

	// load assets
	if err := g.loadAssets(g.cfg.AssetsPath); err != nil {
		log.WithError(err).Error("Couldn't load assets")
		return false
	}

	// init channels
	g.msgChan = make(chan messages.ClientMessage)
	g.loopCloseChan = make(chan struct{})

	// creates the client registry
	g.clients = protocol.NewClientRegistry()

	// setup the telnet server
	if len(g.cfg.TelnetPort) > 0 {
		g.telnetChan = make(chan TelnetRequest)
		g.telnet = protocol.NewTelnetServer(g.cfg.TelnetPort, g.clients)
		g.setTelnetHandlers()
	}

	// setup TCP server
	rootHandler := func(msg *messages.Message, clientId uint32) error {
		// forward incoming messages to the game loop
		g.msgChan <- messages.ClientMessage{msg, clientId}
		return nil
	}
	g.server = *protocol.NewServer(g.cfg.Port, rootHandler, g.clients, g.telnet)
	return true
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
 * loadAssets will load all the needed assets from the specifiec Surviveler
 * package
 */
func (g *Game) loadAssets(path string) error {

	if len(path) == 0 {
		return fmt.Errorf("Can't start without a specified assets path")
	}
	g.assets = resource.NewSurvivelerPackage(g.cfg.AssetsPath)
	if err := g.worldMap.LoadFrom(g.assets); err != nil {
		return err
	}
	log.WithField("path", path).Info("Assets loaded successfully")
	return nil
}

/*
 * stop cleanups the server and exits the various loops
 */
func (g *Game) stop() {
	g.server.Stop()

	// stop game loop
	log.Info("Stopping game loop")
	g.loopCloseChan <- struct{}{}
	close(g.loopCloseChan)
}
