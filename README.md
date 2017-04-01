Surviveler
==========
Surviveler is a real-time role playing game in which players face a zombie
apocalypse while being trapped inside the building of an IT company named
Develer Corporation.


# Assets
Game data is *not* included in this repository and is not publicly available,
you'll need to obtain your copy of game assets via one of authorized game
distribution services. In case you already have a licensed copy of the game,
then you can use the assets from it either by copying them or creating a symlink
to `data` directory in project's root, for example:

    ln -s /path/to/data data


# Quick setup
A convenience bootstrap script is provided to quickly setup the project by
automatically downloading and building dependencies and installing client and
server executables into a local directory. As the rest of the project, it
requires Python 3.6 minimum, and could be executed by simply issuing the
following command from the project's root directory:

    python3.6 bootstrap.py


# Surviveler server

## Requirements

### Go Version
Go 1.6 is preferred, or Go 1.5 with [**Vendor Experiment**](https://medium.com/@freeformz/go-1-5-s-vendor-experiment-fd3e830f52c3#.ks6p4locq).

### Go dependencies management
It is the developer responsibility to maintain the content of the *version
controlled* `src/server/vendor` directory, by keeping updated the set of Git
submodules required by the server.

## Build

### Set your $GOPATH
Set your `$GOPATH` to absolute path to the directory where this README file is
located, a convenient bash command for this could be:

    export GOPATH=$PWD


### Build and install
In order to build, at once, the dependencies and the server executable
(originally called `server`), just type:

    go install server

On success, as for any other Go project, `bin/` and `pkg/` directories will be
created where binaries and build files will be placed.


## Run
To start the server, just run:

    bin/server

*NOTE*: The server will need game assets to be in `data/` directory.

### Configuration
You can specify a certain number of options at server startup, a short usage
help is available by specifying `-h` flag when running the server:

    $ bin/server -h
    NAME:
       server - Surviveler server

    USAGE:
       server [global options] command [command options] [arguments...]

    VERSION:
       0.0.0

    COMMANDS:
    GLOBAL OPTIONS:
       --port value                 Server listening port (TCP)
       --log-level value            Server logging level (Debug, Info, Warning, Error)
       --logic-tick-period value    Period in millisecond of the ticker that updates game logic (default: 0)
       --send-tick-period value     Period in millisecond of the ticker that sends the gamestate to clients (default: 0)
       --time-factor value          Game time speed multiplier (default: 0)
       --night-starting-time value  The night starting time in minutes from midnight (default: 0)
       --night-ending-time value    The night ending time in minutes from midnight (default: 0)
       --game-starting-time value   The games tarting time in minutes from midnight (default: 0)
       --telnet-port value          Any port different than 0 enables the telnet server (disabled by defaut)
       --assets value               Path to the game assets package
       --inifile value              Path to the server configuration file
       --help, -h                   show help
       --version, -v                print the version

Example of server port change:

    $ bin/server --port 12345

Every command line flag can also be specified in a `.ini` file, which keys are
the same than the command line flags. Inifile sections are ignored. In order to
instruct the server to read the configuration parameters from file, provide the
path to the ini file with the `--config` flag, as in:

    $ bin/server --inifile /home/surviveler/home-lan-party.ini


### Admin mode with the telnet server
The embedded telnet server is enabled by setting the `telnet-port` option.

    $ bin/server --telnet-port 2244

To use the telnet interface, start your favourite telnet client by specifying
the configured port:

    $ telnet server-ip 2244

Issue `help` on the telnet line to have a list of available commands, then `help
command` or `command -h` or also `command --help` which will provide you with
the list of *UNIX-like* options accepted by command in question.

Example session:

    surviveler> clients
    connected clients:
     * John Doe - 0
     * Jane Doe - 1

    surviveler> kick -id 0
    client 0 has been kicked out

Enjoy!


# Surviveler client
The client is written in Python language and has a number of external
dependencies. First thing to do is to create an isolated environment for
development and install the needed dependencies. Common setup routines are given
below for Bash and Fish shell users.

*NOTE*: Python 3.5+ is required.

## Using virtualenv or `venv` Python module
Ensure you have `virtualenv` utility installed and then just type:

    virtualenv --python python3.5 .

The `venv` Python module could be used too for the purpose:

    python3.5 -m venv .

Once done, to make the just created environment active source the activation
script:

    # Bash
    . bin/activate

    # Fish
    . bin/activate.fish


## Using virtualfish
To use the fish shell at your best you should install globally virtualfish with

    pip install virtualfish

    # Create the environment and activate it (python3 is the python executable you
    # want to use)
    vf new -p python3 surviveler
    vf activate surviveler

    # When in surviveler/client with the environment activated you can optionally
    # connect it so that it's being activated autmatically every time you enter in
    # the directory
    vf connect

Congratulations, you have a working environment using virtualfish.


## Installing dependencies with pip
Once the environment is set up and active, the following command should do the
trick.

    pip install -r requirements.txt


## Running
To start the client, execute `main.py` with the interpreter installed in
development environment from client's top directory:

    python src/client/main.py

*NOTE*: The client will need game assets to be in `data/` directory.

# Configuration
It is possible to tweak various game settings by modifying the
`config/game.ini` config file. Some useful parameters that can be changed are:

## `[Network]`
Network related configuration section.

### `ServerIPAddress`
IP address of the server to connect to.

## `[Logging]`
Game logging system configuration section.

### `Level`
Is the level of logging for the client, possible values are:

  * `NOTSET`: I have no idea about what this level means, actually.
  * `DEBUG`: huge amount of noise, useful for debug, useless for anything else
    and *slows the game a lot*.
  * `INFO`: main pieces of information about the game. No spam.
  * `WARNING`: not used yet.
  * `ERROR`: not used yet.
  * `CRITICAL`: not used yet.
