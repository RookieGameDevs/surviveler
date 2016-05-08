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
	DefaultPort     = "1234"
	DefaultLogLevel = "Debug"
)

var (
	Port = flag.String("Port", DefaultPort,
		"Server listening port (TCP)")
	LogLevel = flag.String("LogLevel", DefaultLogLevel,
		"Server logging level (Debug, Info, Warning, Error)")
)

/*
 * Config contains all the configurable server-specific game settings
 */
type Config struct {
	Port     string
	LogLevel log.Level
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
