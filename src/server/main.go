/*
 * Surviveler
 * game entry point
 */
package main

import (
	"os"
	"server/surviveler"

	log "github.com/Sirupsen/logrus"
	"github.com/go-ini/ini"
	"github.com/urfave/cli"
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
	cfg := surviveler.NewConfig()

	// command line interface setup
	app := cli.NewApp()
	app.Name = "server"
	app.Usage = "Surviveler server"
	app.Flags = configFlags()
	app.Action = func(c *cli.Context) error {
		// read config file
		if inifile := c.String("inifile"); inifile != "" {
			if err := ini.MapToWithMapper(&cfg, ini.AllCapsUnderscore, inifile); err != nil {
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
		if c.IsSet("time-factor") {
			cfg.TimeFactor = c.Int("time-factor")
		}
		if c.IsSet("night-starting-time") {
			cfg.NightStartingTime = c.Int("night-starting-time")
		}
		if c.IsSet("night-ending-time") {
			cfg.NightEndingTime = c.Int("night-ending-time")
		}
		if c.IsSet("game-starting-time") {
			cfg.GameStartingTime = c.Int("game-starting-time")
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
		inst := surviveler.NewGame(cfg)
		if inst != nil {
			// start the game
			log.Info("Starting game...")
			inst.Start()
		} else {
			log.Fatal("Game startup failed")
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
		cli.IntFlag{
			Name:  "time-factor",
			Usage: "Game time speed multiplier",
		},
		cli.IntFlag{
			Name:  "night-starting-time",
			Usage: "The night starting time in minutes from midnight",
		},
		cli.IntFlag{
			Name:  "night-ending-time",
			Usage: "The night ending time in minutes from midnight",
		},
		cli.IntFlag{
			Name:  "game-starting-time",
			Usage: "The games tarting time in minutes from midnight",
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
