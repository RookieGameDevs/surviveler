/*
 * Surviveler protocol package
 * telnet command controller
 */
package protocol

import (
	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/telgo"
)

type TelnetServer struct {
	Port string
}

func hello(c *telgo.Client, args []string, hostname string) bool {
	c.Sayln("%s @ (%s)", c.UserData.(string), hostname)
	log.WithFields(log.Fields{
		"args":     args,
		"hostname": hostname,
	}).Info("in hello")
	return false
}

func (tns *TelnetServer) Start() {

	globalUserdata := "test"
	cmdlist := make(telgo.CmdList)
	cmdlist["hello"] = func(c *telgo.Client, args []string) bool { return hello(c, args, globalUserdata) }
	s := telgo.NewServer(":"+tns.Port, "surviveler> ", cmdlist, "anonymous")
	if err := s.Run(); err != nil {
		log.WithError(err).Error("Telnet server error")
	}
}
