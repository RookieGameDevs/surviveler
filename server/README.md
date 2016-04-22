# Surviveler. The award winning game. Probably.

## Requirements

### Go Version

Go 1.6 is preferred, or Go 1.5 with [**Vendor Experiment**](https://medium.com/@freeformz/go-1-5-s-vendor-experiment-fd3e830f52c3#.ks6p4locq).

### Go dependencies management

It is the developer responsibility to maintain the content of the *version
controlled* `surviveler/server/vendor` directory.

## Build

Inside `surviveler/server` directory, this will build and place the server
executable in `$GOBIN`

```
go install
```

## Run

From $GOPATH/bin:

```
./server
```

Or, easier, if you have $GOPATH/bin in your `$PATH`, from anywhere:

```
server
```
