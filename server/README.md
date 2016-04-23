# Surviveler server.

## Requirements

### Go Version

Go 1.6 is preferred, or Go 1.5 with [**Vendor Experiment**](https://medium.com/@freeformz/go-1-5-s-vendor-experiment-fd3e830f52c3#.ks6p4locq).

### Go dependencies management

It is the developer responsibility to maintain the content of the *version
controlled* `src/server/vendor` directory.

## Build

Set your `$GOPATH` to /path/to/surviveler/server directory (where this README
file is located) and then issue:

```
go install
```

On success, as for any other Go project, `bin/` and `pkg/` directories will be
created where binaries and build files will be placed.

## Run

To start the server, just run

```
bin/server
```
