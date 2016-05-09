/*
 * Surviveler game package
 * configuration
 */
package game

import (
	"flag"
	"fmt"
	log "github.com/Sirupsen/logrus"
	"github.com/vharitonsky/iniflags"
)

var (
	DefaultPort            = "1234"
	DefaultLogLevel        = "Debug"
	DefaultLogicTickPeriod = 10
	DefaultSendTickPeriod  = 100
)

var (
	Port = flag.String("Port", DefaultPort,
		"Server listening port (TCP)")
	LogLevel = flag.String("LogLevel", DefaultLogLevel,
		"Server logging level (Debug, Info, Warning, Error)")
	LogicTickPeriod = flag.Int("LogicTickPeriod", DefaultLogicTickPeriod,
		"Period in millisecond of the ticker that updates game logic")
	SendTickPeriod = flag.Int("SendTickPeriod", DefaultSendTickPeriod,
		"Period in millisecond of the ticker that send the gamestate to clients")
)

/*
 * Config contains all the configurable server-specific game settings
 */
type Config struct {
	Port            string
	LogLevel        log.Level
	SendTickPeriod  int
	LogicTickPeriod int
}

/*
 * ParseConfig parses the configuration settings, fills and returns a Config
 * struct. Settings are read and merged from, (by precedence):
 * - standard Go flags (command line flags)
 * - ini file values (if any)
 * - default values
 */
func ParseConfig() (cfg Config) {
	iniflags.Parse()

	// fill the Config struct
	cfg = Config{}
	cfg.Port = *Port
	cfg.SendTickPeriod = *SendTickPeriod
	cfg.LogicTickPeriod = *LogicTickPeriod

	if ll, err := log.ParseLevel(*LogLevel); err == nil {
		cfg.LogLevel = ll
	} else {
		fmt.Printf("Unknown log level: %v, using default %v\n", *LogLevel, DefaultLogLevel)
		cfg.LogLevel, err = log.ParseLevel(DefaultLogLevel)
		if err != nil {
			panic(err)
		}
	}
	return
}
