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
)

type TelnetServer struct {
	port     string
	commands map[string]flag.FlagSet
}

/*
 * NewTelnetServer initializes a TelnetServer struct
 */
func NewTelnetServer(port string) *TelnetServer {
	return &TelnetServer{
		port:     port,
		commands: make(map[string]flag.FlagSet),
	}
}

/*
 * Start starts the telnet server. This call is not blocking
 */
func (tns *TelnetServer) Start() {
	cmdList := tns.registerCommands()
	// start the server in a go routine
	s := telgo.NewServer(":"+tns.port, "surviveler> ", cmdList, "anonymous")
	go func() {
		if err := s.Run(); err != nil {
			log.WithError(err).Error("Telnet server error")
		}
	}()
}

func onKick(clientId int32) {
	fmt.Printf("kicking player with client id: %v\n", clientId)
}

/*
 * registerCommands creates and register the list of commands, their options
 * and handlers
 */
func (tns *TelnetServer) registerCommands() telgo.CmdList {
	// set up the list of commands
	commands := make(map[string]telgo.Cmd)

	// register kick command handler
	kickHandler := func(c *telgo.Client, args []string) bool {
		fs := flag.NewFlagSet("kick", flag.ContinueOnError)
		fs.SetOutput(&telnetWriter{c})
		clientId := fs.Int("id", -1, "id of the client to kick")
		fmt.Println("args", args[1:])
		if err := fs.Parse(args[1:]); err == nil {
			onKick(int32(*clientId))
		}
		return false
	}
	commands["kick"] = kickHandler
	return commands
}

/*
 * telnetWriter is an io.Writer implementation that writes on a telnet connection
 * line
 */
type telnetWriter struct{ c *telgo.Client }

/*
 * Write writes the given byte slice on the wrapped telnet connection
 */
func (w telnetWriter) Write(p []byte) (n int, err error) {
	// TODO: protect from trying to write on a closed connection
	//n = bytes.IndexByte(p, 0)
	s := string(p)
	w.c.Sayln(s)
	return len(s), nil
}
