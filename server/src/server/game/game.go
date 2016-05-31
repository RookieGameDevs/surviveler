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
	"sync"
	"syscall"
	"time"
)

/*
 * Game is the main game structure. It also implements the
 * network.ConnEvtHandler interface
 */
type Game struct {
	cfg             Config                      // configuration settings
	server          protocol.Server             // server core
	clients         *protocol.ClientRegistry    // the client registry
	movementPlanner *MovementPlanner            // the movement planner
	assets          resource.SurvivelerPackage  // game assets package
	ticker          time.Ticker                 // the main tick source
	telnet          *protocol.TelnetServer      // if enabled, the telnet server
	telnetChan      chan TelnetRequest          // channel for game related telnet commands
	msgChan         chan messages.ClientMessage // conducts ClientMessage to the game loop
	gameQuitChan    chan struct{}               // to signal the game loop goroutine it must end
	waitGroup       sync.WaitGroup              // wait for the different goroutine to finish
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
	g.gameQuitChan = make(chan struct{})

	// creates the client registry
	g.clients = protocol.NewClientRegistry()

	// setup the telnet server
	if len(g.cfg.TelnetPort) > 0 {
		g.telnetChan = make(chan TelnetRequest)
		g.telnet = protocol.NewTelnetServer(g.cfg.TelnetPort, g.clients)
		g.registerTelnetHandlers()
	}

	// init the movement planner
	g.movementPlanner = NewMovementPlanner(g.gameQuitChan, &g.waitGroup)

	// setup TCP server
	rootHandler := func(msg *messages.Message, clientId uint32) error {
		// forward incoming messages to the game loop
		g.msgChan <- messages.ClientMessage{msg, clientId}
		return nil
	}
	g.server = *protocol.NewServer(g.cfg.Port, rootHandler, g.clients, g.telnet, &g.waitGroup)

	return true
}

/*
 * loadAssets load the assets package
 */
func (g *Game) loadAssets(path string) error {
	if len(path) == 0 {
		return fmt.Errorf("Can't start without a specified assets path")
	}
	g.assets = resource.NewSurvivelerPackage(g.cfg.AssetsPath)
	log.WithField("path", path).Info("Assets loaded successfully")
	return nil
}

/*
 * Start starts the server and game loops
 */
func (g *Game) Start() {
	// start everything
	g.server.Start()

	// start the movement planner
	g.movementPlanner.Start()

	// start the game loop (will return immedialtely as the game loop runs
	// in a goroutine)
	if err := g.loop(); err != nil {
		log.WithError(err).Error("Game state initialization failed...")
	} else {
		// game loop started, make this goroutine wait for
		// for an operating system signal
		chSig := make(chan os.Signal)
		defer close(chSig)
		signal.Notify(chSig, syscall.SIGINT, syscall.SIGTERM)
		log.WithField("signal", <-chSig).Warn("Received termination signal")
	}

	g.stop()
}

/*
 * stop cleanups the server and exits the various loops
 */
func (g *Game) stop() {
	g.server.Stop()

	close(g.gameQuitChan)
	g.waitGroup.Wait()
}
