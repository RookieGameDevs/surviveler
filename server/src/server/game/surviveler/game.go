/*
 * Surviveler game package
 * game entry & exit points
 */
package surviveler

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"os"
	"os/signal"
	"runtime"
	"server/game"
	"server/game/ai"
	"server/game/events"
	msg "server/game/messages"
	"server/game/protocol"
	"server/game/resource"
	"sync"
	"syscall"
	"time"
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
	eventManager    *events.EventManager       // event manager
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
	g.state = newGameState(g, int16(cfg.GameStartingTime))
	if err := g.state.init(g.assets); err != nil {
		log.WithError(err).Error("Couldn't initialize gamestate")
		return nil
	}

	// init channels
	g.msgChan = make(chan msg.ClientMessage)
	g.quitChan = make(chan struct{})

	g.eventManager = events.NewEventManager()

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

	// init the movement planner (and provide it to the game state)
	g.movementPlanner = game.NewMovementPlanner(g)
	g.state.movementPlanner = g.movementPlanner

	// init the AI director
	g.ai = ai.NewAIDirector(g, int16(cfg.NightStartingTime), int16(cfg.NightEndingTime))

	// setup TCP server
	rootHandler := func(imsg *msg.Message, clientId uint32) error {
		// forward incoming messages to the game loop
		g.msgChan <- msg.ClientMessage{imsg, clientId}
		return nil
	}
	g.server = *protocol.NewServer(g.cfg.Port, rootHandler, g.clients, g.telnet, &g.wg, g.eventManager.PostEvent)

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

func (g *survivelerGame) State() game.GameState {
	return g.state
}

func (g *survivelerGame) QuitChan() chan struct{} {
	return g.quitChan
}

func (g *survivelerGame) MessageChan() chan msg.ClientMessage {
	return g.msgChan
}

func (g *survivelerGame) PostEvent(evt *events.Event) {
	g.eventManager.PostEvent(evt)
}

func (g *survivelerGame) Pathfinder() *game.Pathfinder {
	return g.pathfinder
}

func (g *survivelerGame) WaitGroup() *sync.WaitGroup {
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
