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
	msg "server/game/messages"
	"server/game/protocol"
	"server/game/resource"
	"sync"
	"syscall"
	"time"
)

/*
 * Game is the main game structure, entry and exit points
 */
type Game struct {
	cfg             Config                     // configuration settings
	server          protocol.Server            // server core
	clients         *protocol.ClientRegistry   // the client registry
	movementPlanner *MovementPlanner           // the movement planner
	assets          resource.SurvivelerPackage // game assets package
	ticker          time.Ticker                // the main tick source
	telnet          *protocol.TelnetServer     // if enabled, the telnet server
	telnetReq       chan TelnetRequest         // channel for game related telnet commands
	telnetDone      chan error                 // signals the end of a telnet request
	msgChan         chan msg.ClientMessage     // conducts ClientMessage to the game loop
	gameQuit        chan struct{}              // to signal the game loop goroutine it must end
	wg              sync.WaitGroup             // wait for the different goroutine to finish
}

/*
 * Setup initializes the different game subsystems
 */
func (g *Game) Setup(cfg Config) bool {
	// copy configuration
	g.cfg = cfg

	// setup logger
	var err error
	var lvl log.Level
	if lvl, err = log.ParseLevel(g.cfg.LogLevel); err != nil {
		log.WithFields(log.Fields{"level": g.cfg.LogLevel, "default": DefaultLogLevel}).Warn("unknown log level, using default")
		g.cfg.LogLevel = DefaultLogLevel
		lvl, _ = log.ParseLevel(DefaultLogLevel)
	}
	log.StandardLogger().Level = lvl

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
	g.msgChan = make(chan msg.ClientMessage)
	g.gameQuit = make(chan struct{})

	// creates the client registry
	g.clients = protocol.NewClientRegistry()

	// setup the telnet server
	if len(g.cfg.TelnetPort) > 0 {
		g.telnetReq = make(chan TelnetRequest)
		g.telnetDone = make(chan error)
		g.telnet = protocol.NewTelnetServer(g.cfg.TelnetPort, g.clients)
		g.registerTelnetHandlers()
	}

	// init the movement planner
	g.movementPlanner = NewMovementPlanner(g)

	// setup TCP server
	rootHandler := func(imsg *msg.Message, clientId uint32) error {
		// forward incoming messages to the game loop
		g.msgChan <- msg.ClientMessage{imsg, clientId}
		return nil
	}
	g.server = *protocol.NewServer(g.cfg.Port, rootHandler, g.clients, g.telnet, &g.wg)

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
 * stop cleanups the servers and exits the various loops
 *
 * Main tcp server and telnet server are successively closed, each in a
 * blocking call to Stop that let them cleanups the various goroutines and
 * connections still opened.
 */
func (g *Game) stop() {
	g.server.Stop()
	if g.telnet != nil {
		g.telnet.Stop()
	}

	close(g.gameQuit)
	g.wg.Wait()
}
