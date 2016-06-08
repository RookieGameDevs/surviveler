/*
 * Surviveler protocol package
 * telnet command controller
 */
package protocol

import (
	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/telgo"
	"github.com/urfave/cli"
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
func (tns *TelnetServer) Start(wg *sync.WaitGroup) {
	globalHandler := func(c *telgo.Client, args []string) bool {
		tw := telnetWriter{c}
		tns.CliApp.Writer = &tw
		tns.CliApp.ErrWriter = &tw
		tns.CliApp.Run(append([]string{""}, args...))
		return false
	}

	// start the server in a goroutine
	tns.server = telgo.NewServer(":"+tns.port, "surviveler> ", globalHandler, "anonymous")
	go func() {
		wg.Add(1)
		defer func() {
			log.Info("Stopping admin telnet server")
			wg.Done()
		}()
		log.Info("Starting admin telnet server")
		if err := tns.server.Run(); err != nil {
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
