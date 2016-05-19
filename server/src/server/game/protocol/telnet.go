/*
 * Surviveler protocol package
 * telnet command controller
 */
package protocol

import (
	"flag"
	"fmt"
	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/telgo"
	"io"
)

type TelnetServer struct {
	port     string               // port on which listening
	commands map[string]TelnetCmd // the registered telnet commands
	registry *ClientRegistry      // the unique client registry
}

type TelnetHandlerFunc func(io.Writer)

type TelnetCmd struct {
	Name    string            // command name
	Descr   string            // command description
	Parms   flag.FlagSet      // command parameters, in an embedded flag set
	Handler TelnetHandlerFunc // handler function
}

func NewTelnetCmd(name string) TelnetCmd {
	return TelnetCmd{
		Name:  name,
		Descr: "",
		Parms: *flag.NewFlagSet(name, flag.ContinueOnError),
	}
}

/*
 * NewTelnetServer initializes a TelnetServer struct
 */
func NewTelnetServer(port string, registry *ClientRegistry) *TelnetServer {
	return &TelnetServer{
		port:     port,
		commands: make(map[string]TelnetCmd),
		registry: registry,
	}
}

/*
 * Start starts the telnet server. This call is not blocking
 */
func (tns *TelnetServer) Start() {

	globalHandler := func(c *telgo.Client, args []string) bool {
		tw := &telnetWriter{c}
		if cmd, ok := tns.commands[args[0]]; ok {
			// cmd handler
			cmd.Parms.SetOutput(tw)
			cmd.Parms.Parse(args[1:])
			cmd.Handler(tw)
		} else {
			subcmd := ""
			if len(args) > 1 {
				subcmd = args[1]
			}
			if cmd, ok = tns.commands[subcmd]; ok && args[0] == "help" {
				cmd.Parms.SetOutput(tw)
				cmd.Parms.PrintDefaults()
			} else {
				c.Sayln(tns.usage())
			}
		}
		return false
	}

	// start the server in a go routine
	s := telgo.NewServer(":"+tns.port, "surviveler> ", globalHandler, "anonymous")
	go func() {
		if err := s.Run(); err != nil {
			log.WithError(err).Error("Telnet server error")
		}
	}()
}

/*
 * RegisterCommand register a new telnet command, and its handler. flags is a configured
 * FlagSet describing the command and its arguments
 */
func (tns *TelnetServer) RegisterCommand(cmd TelnetCmd) {
	tns.commands[cmd.Name] = cmd
}

/*
 * usage prints the list registered telnet commands and their description
 */
func (tns *TelnetServer) usage() string {
	h := "available commands:\n"
	for cmdName, cmd := range tns.commands {
		h = h + fmt.Sprintf("  %-18s%s\n", cmdName, cmd.Descr)
	}
	h = h + fmt.Sprintf("  %-18s%s\n", "help", "this help text")
	return h
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
	w.c.Sayln(s)
	return len(s), nil
}

/*
 * TelnetRequest represents the type and content of a telnet request, and a way to
 * reply to it
 */
type TelnetRequest struct {
	Type    uint32
	Content interface{}
	Writer  io.Writer
}

const (
	DumpGameStateId uint32 = 0 + iota
)
