/*
 * Surviveler package
 * game entry & exit points
 */
package surviveler

import (
	"fmt"
	"os"
	"os/signal"
	"runtime"
	"server/events"
	"server/protocol"
	"server/resource"
	"sync"
	"syscall"
	"time"

	log "github.com/Sirupsen/logrus"
)

/*
 * Game is the main game structure, entry and exit points
 */
type Game struct {
	cfg          Config                   // configuration settings
	server       *protocol.Server         // server core
	clients      *protocol.ClientRegistry // the client registry
	assets       resource.Package         // game assets package
	ticker       time.Ticker              // the main tick source
	telnet       *protocol.TelnetServer   // if enabled, the telnet server
	telnetReq    chan TelnetRequest       // channel for game related telnet commands
	telnetDone   chan error               // signals the end of a telnet request
	quitChan     chan struct{}            // to signal the game loop goroutine it must end
	eventManager *events.Manager          // event manager
	wg           sync.WaitGroup           // wait for the different goroutine to finish
	state        *GameState               // the game state
	pathfinder   *Pathfinder              // pathfinder
	ai           *AIDirector              // AI director
	gameData     *gameData
}

/*
 * Setup initializes the different game subsystems
 */
func NewGame(cfg Config) *Game {
	g := new(Game)

	// copy configuration
	g.cfg = cfg

	var (
		err error
		lvl log.Level
	)
	// setup logger
	if lvl, err = log.ParseLevel(g.cfg.LogLevel); err != nil {
		log.WithFields(log.Fields{
			"level":   g.cfg.LogLevel,
			"default": DefaultLogLevel,
		}).Warn("unknown log level, using default")
		g.cfg.LogLevel = DefaultLogLevel
		lvl, _ = log.ParseLevel(DefaultLogLevel)
	}
	log.StandardLogger().Level = lvl

	// dump config
	log.WithField("cfg", g.cfg).Info("Game configuration")

	// setup go runtime
	runtime.GOMAXPROCS(runtime.NumCPU())

	// load assets
	g.gameData, err = g.loadAssets(g.cfg.AssetsPath)
	if err != nil {
		log.WithError(err).Error("Couldn't load assets")
		return nil
	}

	// initialize the gamestate
	g.state = newGameState(g, int16(cfg.GameStartingTime))
	if err := g.state.init(g.gameData); err != nil {
		log.WithError(err).Error("Couldn't initialize gamestate")
		return nil
	}

	// init channels
	g.quitChan = make(chan struct{})

	g.eventManager = events.NewManager()

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
	g.pathfinder = NewPathfinder(g)

	// init the AI director
	g.ai = NewAIDirector(g, int16(cfg.NightStartingTime), int16(cfg.NightEndingTime))
	g.server = protocol.NewServer(g.cfg.Port, g.clients, g.telnet, &g.wg, g.clients)

	// this will be called after a new player has successfully joined the game
	g.server.OnPlayerJoined(func(ID uint32, playerType uint8) {
		g.PostEvent(
			events.NewEvent(
				events.PlayerJoinId,
				events.PlayerJoin{Id: ID, Type: playerType}))
	})

	// this will be called after a player has effectively left the game
	g.server.OnPlayerLeft(func(ID uint32) {
		g.PostEvent(
			events.NewEvent(
				events.PlayerLeaveId,
				events.PlayerLeave{Id: ID}))
	})

	g.registerMsgHandlers()
	return g
}

/*
 * loadAssets load the assets package
 */
func (g *Game) loadAssets(path string) (*gameData, error) {
	if len(path) == 0 {
		return nil, fmt.Errorf("can't start without a specified assets path")
	}
	pkg, err := resource.OpenFSPackage(g.cfg.AssetsPath)
	if err != nil {
		return nil, fmt.Errorf("can't open assets %v", g.cfg.AssetsPath)
	}
	g.assets = pkg

	// load game assets
	gameData, err := newGameData(g.assets)
	if err != nil {
		return nil, err
	}

	log.WithField("path", path).Info("Assets loaded successfully")
	return gameData, nil
}

/*
 * Start starts the server and game loops
 */
func (g *Game) Start() {
	// start everything
	g.server.Start()

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

func (g *Game) State() *GameState {
	return g.state
}

func (g *Game) QuitChan() chan struct{} {
	return g.quitChan
}

func (g *Game) PostEvent(evt *events.Event) {
	g.eventManager.PostEvent(evt)
}

func (g *Game) Pathfinder() *Pathfinder {
	return g.pathfinder
}

func (g *Game) WaitGroup() *sync.WaitGroup {
	return &g.wg
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

	close(g.quitChan)
	g.wg.Wait()
}
