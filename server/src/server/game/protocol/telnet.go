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

func onTelnetKick(clientId int32, w io.Writer) {
	if clientId < 0 {
		io.WriteString(w, fmt.Sprintf("invalid client id: %v\n", clientId))
	} else {
		// try kick client
		io.WriteString(w, fmt.Sprintf("client %v has been kicked out\n", clientId))
	}
}

func onTelnetClients(w io.Writer) {
	io.WriteString(w, fmt.Sprintf("this is the list of connected clients\n"))
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
		tw := &telnetWriter{c}
		fs.SetOutput(tw)
		clientId := fs.Int("id", -1, "id of the client to kick (integer)")
		if err := fs.Parse(args[1:]); err == nil {
			onTelnetKick(int32(*clientId), tw)
		}
		return false
	}
	commands["kick"] = kickHandler

	// register clients command handler
	clientsHandler := func(c *telgo.Client, args []string) bool {
		fs := flag.NewFlagSet("clients", flag.ContinueOnError)
		tw := &telnetWriter{c}
		fs.SetOutput(tw)
		if err := fs.Parse(args[1:]); err == nil {
			onTelnetClients(tw)
		}
		return false
	}
	commands["clients"] = clientsHandler

	// register help command handler
	helpHandler := func(c *telgo.Client, args []string) bool {
		tw := &telnetWriter{c}
		io.WriteString(tw, "usage:")
		io.WriteString(tw, "\tkick -id clientId    kick a client")
		io.WriteString(tw, "\tclients              shows list of clients")
		io.WriteString(tw, "\thelp [cmdname]       get help")
		io.WriteString(tw, "\n")
		if len(args) > 1 {
			// help about a specific command
			for cmd, cb := range commands {
				if args[1] == cmd {
					args[0] = cmd
					args[1] = "--help"
					cb(c, args)
				}
			}
		}
		return false
	}
	commands["help"] = helpHandler

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
