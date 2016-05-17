# Surviveler server

## Requirements

### Go Version

Go 1.6 is preferred, or Go 1.5 with [**Vendor Experiment**](https://medium.com/@freeformz/go-1-5-s-vendor-experiment-fd3e830f52c3#.ks6p4locq).

### Go dependencies management

It is the developer responsibility to maintain the content of the *version
controlled* `src/server/vendor` directory, by keeping updated the set of Git
submodules required by the server.

## Build

Pull out the Git submodules dependencies:

```
git submodules init
git submodules update
```

### Set your $GOPATH

Set your `$GOPATH` to `/path/to/surviveler/server` directory (where this README
file is located).


### Build and install

Change to the directory where resides the file `main.go`, that is
`/path/to/surviveler/server/src/server` and then issue:

```
go install
```

On success, as for any other Go project, `bin/` and `pkg/` directories will be
created where binaries and build files will be placed.

## Run

To start the server, just run:

```
bin/server
```

### Configuration

You can set the server options in two ways and a summary of the
possible options is printed after issuing, or by reading the, hopefully updated
`server.ini`:

```
$ server -h
Usage of server:
  -config string
        Path to ini config for using in go flags.
  -log-level string
        Server logging level (Debug, Info, Warning, Error) (default "Debug")
  -logic-tick-period int
        Period in millisecond of the ticker that updates game logic (default 10)
  -port string
        Server listening port (TCP) (default "1234")
  -send-tick-period int
        Period in millisecond of the ticker that send the gamestate to clients (default 100)
  -telnet-port string
        Any port different than 0 enables the telnet server (disabled by defaut)
```

Example:

```
bin/server -port 12345
```

Every command line flag can also be defined in a *ini* file, which keys are the
same than the command line flags. Inifile sections are ignored.  
Provides the path to the ini file path with the `-config` flag, as in:

```
bin/server -config /path/to/server.ini
```

### Admin mode with the telnet server

The embedded telnet server is enabled by setting the `telnet-port` option.

```
bin/server -telnet-port 2244
```

Then, start your favourite telnet client:
```
telnet server-ip 2244
```
Issue `help` on the telnet line to have a list of available commands, then
`help command` or `command -h` or also `command --help` with provide you
with the list of *unix-like* options accepted by this specific command.
Example session:
```
surviveler> clients
connected clients:
 * John Doe - 0
 * Jane Doe - 1
 
surviveler> kick -id 0
client 0 has been kicked out
```
Enjoy!

