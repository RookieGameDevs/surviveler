/*
 * Surviveler game package
 * configuration
 */
package game

const DefaultLogLevel string = "Debug"

/*
 * Config contains all the configurable server-specific game settings
 */
type Config struct {
	Port            string
	LogLevel        string
	SendTickPeriod  int
	LogicTickPeriod int
	TelnetPort      string
	AssetsPath      string
}

/*
 * NewConfig returns a Config instance, pre-filled with default values
 */
func NewConfig() Config {
	return Config{
		Port:            "1234",
		LogLevel:        "Info",
		SendTickPeriod:  100,
		LogicTickPeriod: 10,
		TelnetPort:      "1235",
		AssetsPath:      "../data",
	}
}
