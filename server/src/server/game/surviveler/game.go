/*
 * Surviveler game package
 * game entry & exit points
 */
package surviveler

import (
	"fmt"
	"os"
	"os/signal"
	"runtime"
	"server/game"
	"server/game/ai"
	msg "server/game/messages"
	"server/game/protocol"
	"server/game/resource"
	"sync"
	"syscall"
	"time"

	log "github.com/Sirupsen/logrus"
)

/*
 * survivelerGame is the main game structure, entry and exit points
 */
type survivelerGame struct {
	cfg             game.Config                // configuration settings
	server          protocol.Server            // server core
	clients         *protocol.ClientRegistry   // the client registry
	assets          resource.SurvivelerPackage // game assets package
	ticker          time.Ticker                // the main tick source
	telnet          *protocol.TelnetServer     // if enabled, the telnet server
	telnetReq       chan TelnetRequest         // channel for game related telnet commands
	telnetDone      chan error                 // signals the end of a telnet request
	msgChan         chan msg.ClientMessage     // conducts ClientMessage to the game loop
	quitChan        chan struct{}              // to signal the game loop goroutine it must end
	wg              sync.WaitGroup             // wait for the different goroutine to finish
	state           *gamestate                 // the game state
	movementPlanner *game.MovementPlanner      // the movement planner
	pathfinder      *game.Pathfinder           // pathfinder
	ai              *ai.AIDirector             // AI director
}

/*
 * Setup initializes the different game subsystems
 */
func NewGame(cfg game.Config) game.Game {
	g := new(survivelerGame)

	// copy configuration
	g.cfg = cfg

	// setup logger
	var err error
	var lvl log.Level
	if lvl, err = log.ParseLevel(g.cfg.LogLevel); err != nil {
		log.WithFields(log.Fields{
			"level":   g.cfg.LogLevel,
			"default": game.DefaultLogLevel,
		}).Warn("unknown log level, using default")
		g.cfg.LogLevel = game.DefaultLogLevel
		lvl, _ = log.ParseLevel(game.DefaultLogLevel)
	}
	log.StandardLogger().Level = lvl

	// dump config
	log.WithField("cfg", g.cfg).Info("Game configuration")

	// setup go runtime
	runtime.GOMAXPROCS(runtime.NumCPU())

	// load assets
	if err := g.loadAssets(g.cfg.AssetsPath); err != nil {
		log.WithError(err).Error("Couldn't load assets")
		return nil
	}

	// initialize the gamestate
	g.state = newGameState()
	if err := g.state.init(g.assets); err != nil {
		log.WithError(err).Error("Couldn't initialize gamestate")
		return nil
	}

	// init channels
	g.msgChan = make(chan msg.ClientMessage)
	g.quitChan = make(chan struct{})

	// creates the client registry
	allocId := func() uint32 {
		return g.state.allocEntityId()
	}
	g.clients = protocol.NewClientRegistry(allocId)

	// setup the telnet server
	if len(g.cfg.TelnetPort) > 0 {
		g.telnetReq = make(chan TelnetRequest)
		g.telnetDone = make(chan error)
		g.telnet = protocol.NewTelnetServer(g.cfg.TelnetPort, g.clients)
		g.registerTelnetHandlers()
	}

	// initialize the pathfinder module
	g.pathfinder = game.NewPathfinder(g)

	// init the movement planner
	g.movementPlanner = game.NewMovementPlanner(g)

	// init the AI director
	g.ai = ai.NewAIDirector(g)

	// setup TCP server
	rootHandler := func(imsg *msg.Message, clientId uint32) error {
		// forward incoming messages to the game loop
		g.msgChan <- msg.ClientMessage{imsg, clientId}
		return nil
	}
	g.server = *protocol.NewServer(g.cfg.Port, rootHandler, g.clients, g.telnet, &g.wg)

	return g
}

/*
 * loadAssets load the assets package
 */
func (g *survivelerGame) loadAssets(path string) error {
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
func (g *survivelerGame) Start() {
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

func (g *survivelerGame) GetState() game.GameState {
	return g.state
}

func (g *survivelerGame) GetQuitChan() chan struct{} {
	return g.quitChan
}

func (g *survivelerGame) GetMessageChan() chan msg.ClientMessage {
	return g.msgChan
}

func (g *survivelerGame) GetPathfinder() *game.Pathfinder {
	return g.pathfinder
}

func (g *survivelerGame) GetWaitGroup() *sync.WaitGroup {
	return &g.wg
}

/*
 * stop cleanups the servers and exits the various loops
 *
 * Main tcp server and telnet server are successively closed, each in a
 * blocking call to Stop that let them cleanups the various goroutines and
 * connections still opened.
 */
func (g *survivelerGame) stop() {
	g.server.Stop()
	if g.telnet != nil {
		g.telnet.Stop()
	}

	close(g.quitChan)
	g.wg.Wait()
}
