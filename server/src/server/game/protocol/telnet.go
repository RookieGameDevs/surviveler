/*
 * Surviveler protocol package
 * telnet command controller
 */
package protocol

import (
	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/telgo"
	"github.com/urfave/cli"
	"net"
	"sync"
)

type TelnetServer struct {
	port     string          // port on which listening
	registry *ClientRegistry // the unique client registry
	server   *telgo.Server
	CliApp   *cli.App
}

/*
 * NewTelnetServer initializes a TelnetServer struct
 */
func NewTelnetServer(port string, registry *ClientRegistry) *TelnetServer {
	tns := TelnetServer{
		port:     port,
		registry: registry,
		CliApp:   cli.NewApp(),
	}
	tns.CliApp.Name = "Surviveler admin console"
	tns.CliApp.Usage = "Control a Surviveler game session from the comfort of your telnet console"
	tns.CliApp.HideVersion = true
	tns.CliApp.CommandNotFound = func(c *cli.Context, s string) {
		cli.ShowAppHelp(c)
	}
	cli.OsExiter = func(int) {}
	return &tns
}

/*
 * Start starts the telnet server.
 *
 * This call is non blocking and starts its own goroutine. When this goroutine
 * is started, the TelnetServer increments the provided waitGroup parameter.
 */
func (tns *TelnetServer) Start(listener *net.TCPListener, wg *sync.WaitGroup) {
	globalHandler := func(c *telgo.Client, args []string) bool {
		tw := telnetWriter{c}
		tns.CliApp.Writer = &tw
		tns.CliApp.ErrWriter = &tw
		tns.CliApp.Run(append([]string{""}, args...))
		return false
	}

	wg.Add(1)
	// start the server in a goroutine
	tns.server = telgo.NewServer("surviveler> ", globalHandler, "anonymous")
	go func() {
		defer func() {
			log.Info("Stopping admin telnet server")
			wg.Done()
		}()
		log.Info("Starting admin telnet server")
		if err := tns.server.Run(listener); err != nil {
			log.WithError(err).Error("Telnet server error")
		}
	}()
}

/*
 * RegisterCommand registers a telnet command
 */
func (tns *TelnetServer) RegisterCommand(cmd *cli.Command) {
	cmd.OnUsageError = tns.CliApp.OnUsageError
	tns.CliApp.Commands = append(tns.CliApp.Commands, *cmd)
}

/*
 * Stop asks the underlying telnet server to quit
 */
func (tns *TelnetServer) Stop() {
	tns.server.Quit()
}

/*
 * telnetWriter is an io.Writer implementation that writes on a telnet connection
 * line
 */
type telnetWriter struct {
	c *telgo.Client
}

/*
 * Write writes the given byte slice on the wrapped telnet connection
 */
func (w telnetWriter) Write(p []byte) (n int, err error) {
	s := string(p)
	w.c.Say(s)
	return len(s), nil
}
