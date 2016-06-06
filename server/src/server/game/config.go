/*
 * Surviveler game package
 * configuration
 */
package game

import (
	log "github.com/Sirupsen/logrus"
	"github.com/urfave/cli"
	"gopkg.in/ini.v2"
	"os"
)

const DefaultLogLevel string = "Debug"

/*
 * Config contains all the configurable server-specific game settings
 */
type Config struct {
	Port            string
	LogLevel        log.Level
	SendTickPeriod  int
	LogicTickPeriod int
	TelnetPort      string
	AssetsPath      string
}

/*
 * fromInifile preloads a cli.Context with values coming from an ini file
 */
func fromInifile(c *cli.Context, filename string) error {
	cfg, err := ini.Load(filename)
	if err != nil {
		return err
	}
	global := cfg.Section("")
	if s := global.Key("port").MustString(""); s != "" {
		c.Set("port", s)
	}
	if s := global.Key("log-level").MustString(""); s != "" {
		c.Set("log-level", s)
	}
	if s := global.Key("telnet-port").MustString(""); s != "" {
		c.Set("telnet-port", s)
	}
	if s := global.Key("assets").MustString(""); s != "" {
		c.Set("assets", s)
	}
	if s := global.Key("send-tick-period").MustString(""); s != "" {
		c.Set("send-tick-period", s)
	}
	if s := global.Key("logic-tick-period").MustString(""); s != "" {
		c.Set("logic-tick-period", s)
	}
	return nil
}

/*
 * ParseConfig parses the configuration settings, fills and returns a Config
 * struct. Settings are read and merged from, (by precedence):
 * - standard Go flags (command line flags)
 * - ini file values (if any)
 * - default values
 */
func ParseConfig() (cfg Config) {
	cfg = Config{}

	var logLevel string
	app := cli.NewApp()
	app.Metadata = make(map[string]interface{})
	app.Metadata["config"] = Config{}
	app.Name = "server"
	app.Usage = "Surviveler server"
	app.Flags = []cli.Flag{
		cli.StringFlag{
			Name:        "port",
			Usage:       "Server listening port (TCP)",
			Value:       "1234",
			Destination: &cfg.Port,
		},
		cli.StringFlag{
			Name:        "log-level",
			Usage:       "Server logging level (Debug, Info, Warning, Error)",
			Destination: &logLevel,
		},
		cli.IntFlag{
			Name:        "logic-tick-period",
			Usage:       "Period in millisecond of the ticker that updates game logic",
			Value:       10,
			Destination: &cfg.LogicTickPeriod,
		},
		cli.IntFlag{
			Name:        "send-tick-period",
			Usage:       "Period in millisecond of the ticker that sends the gamestate to clients",
			Value:       100,
			Destination: &cfg.SendTickPeriod,
		},
		cli.StringFlag{
			Name:        "telnet-port",
			Usage:       "Any port different than 0 enables the telnet server (disabled by defaut)",
			Value:       "",
			Destination: &cfg.TelnetPort,
		},
		cli.StringFlag{
			Name:        "assets",
			Usage:       "Path to the game assets package",
			Value:       "../data",
			Destination: &cfg.AssetsPath,
		},
		cli.StringFlag{
			Name:  "inifile",
			Usage: "Path to the server configuration file",
		},
	}
	app.Action = func(c *cli.Context) error {
		// read config file
		if inifile := c.String("inifile"); inifile != "" {
			if err := fromInifile(c, inifile); err != nil {
				log.WithError(err).Error("Couldn't read config file")
				return err
			}
			log.Warn("other command line flags have no effect in presence of --inifile")
		}

		// fill the Config struct
		cfg.Port = c.String("port")
		cfg.SendTickPeriod = c.Int("send-tick-period")
		cfg.LogicTickPeriod = c.Int("logic-tick-period")
		cfg.TelnetPort = c.String("telnet-port")
		cfg.AssetsPath = c.String("assets")
		if ll, err := log.ParseLevel(logLevel); err == nil {
			cfg.LogLevel = ll
		} else {
			if logLevel != "" {
				log.WithFields(log.Fields{"level": logLevel, "default": DefaultLogLevel}).Warn("Unknown log level, using default")
			}
			logLevel = DefaultLogLevel
			cfg.LogLevel, err = log.ParseLevel(logLevel)
			if err != nil {
				return err
			}
		}
		return nil
	}
	app.Run(os.Args)
	return
}
