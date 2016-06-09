/*
 * Surviveler
 * game entry point
 */
package main

import (
	log "github.com/Sirupsen/logrus"
	"github.com/urfave/cli"
	"gopkg.in/ini.v2"
	"os"
	"server/game"
)

/*
 * runCliApp reads configuration and run the server as a command line app

 * Configuration is read from various sources, merged if needed, and finally
 * passed to the Game instance.
 *
 * By order of precedence, this is how the configuration fields are merged:
 * - command line flags
 * - ini file values (if any)
 * - default values
 *
 * `-h` or `--help` flags is a special case, directly handled by the cli library,
 * it shows the app usage and exits
 */
func runCliApp() error {
	// get configuration, pre-filled with default values
	cfg := game.NewConfig()

	// command line interface setup
	app := cli.NewApp()
	app.Name = "server"
	app.Usage = "Surviveler server"
	app.Flags = configFlags()
	app.Action = func(c *cli.Context) error {
		// read config file
		if inifile := c.String("inifile"); inifile != "" {
			if err := ini.MapToWithMapper(cfg, ini.AllCapsUnderscore, inifile); err != nil {
				log.WithField("inifile", inifile).WithError(err).Error("Couldn't read config file")
				os.Exit(1)
			}
		}

		// override current configuration with the values of
		// the flags provided on the command line
		if c.IsSet("port") {
			cfg.Port = c.String("port")
		}
		if c.IsSet("send-tick-period") {
			cfg.SendTickPeriod = c.Int("send-tick-period")
		}
		if c.IsSet("logic-tick-period") {
			cfg.LogicTickPeriod = c.Int("logic-tick-period")
		}
		if c.IsSet("telnet-port") {
			cfg.TelnetPort = c.String("telnet-port")
		}
		if c.IsSet("assets") {
			cfg.AssetsPath = c.String("assets")
		}
		if c.IsSet("log-level") {
			cfg.LogLevel = c.String("log-level")
		}

		// game setup
		var surviveler game.Game
		if surviveler.Setup(cfg) {
			// start the game
			surviveler.Start()
		}
		return nil
	}
	return app.Run(os.Args)
}

/*
 * configFlags populates and returns a slice with the command line flags
 */
func configFlags() []cli.Flag {
	return []cli.Flag{
		cli.StringFlag{
			Name:  "port",
			Usage: "Server listening port (TCP)",
		},
		cli.StringFlag{
			Name:  "log-level",
			Usage: "Server logging level (Debug, Info, Warning, Error)",
		},
		cli.IntFlag{
			Name:  "logic-tick-period",
			Usage: "Period in millisecond of the ticker that updates game logic",
		},
		cli.IntFlag{
			Name:  "send-tick-period",
			Usage: "Period in millisecond of the ticker that sends the gamestate to clients",
		},
		cli.StringFlag{
			Name:  "telnet-port",
			Usage: "Any port different than 0 enables the telnet server (disabled by defaut)",
		},
		cli.StringFlag{
			Name:  "assets",
			Usage: "Path to the game assets package",
		},
		cli.StringFlag{
			Name:  "inifile",
			Usage: "Path to the server configuration file",
		},
	}
}

func main() {
	runCliApp()
}
