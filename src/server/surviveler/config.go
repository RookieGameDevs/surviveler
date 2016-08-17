/*
 * Surviveler package
 * configuration
 */
package surviveler

const DefaultLogLevel string = "Debug"

/*
 * Config contains all the configurable server-specific game settings
 */
type Config struct {
	Port              string
	LogLevel          string
	SendTickPeriod    int
	LogicTickPeriod   int
	TimeFactor        int
	NightStartingTime int
	NightEndingTime   int
	GameStartingTime  int
	TelnetPort        string
	AssetsPath        string
}

/*
 * NewConfig returns a Config instance, pre-filled with default values
 */
func NewConfig() Config {
	return Config{
		Port:              "1234",
		LogLevel:          "Info",
		SendTickPeriod:    100,
		LogicTickPeriod:   10,
		TimeFactor:        60,
		NightStartingTime: 1080,
		NightEndingTime:   480,
		GameStartingTime:  480,
		TelnetPort:        "1235",
		AssetsPath:        "data",
	}
}
