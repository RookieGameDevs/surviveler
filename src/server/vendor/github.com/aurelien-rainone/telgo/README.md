# Simple Telnet control interface for go applications

This golang ackage contains a simple telnet server which can be used as a
control/debug interface for applications.
The telgo telnet server does all the client handling and runs configurable
commands as go routines. It also supports handling of basic inline telnet
commands used by variaus telnet clients to configure the client connection.
For now every negotiable telnet option will be discarded but the telnet
command IP (interrupt process) is understood and can be used to terminate
long running user commands.

## Status

This is currently on development. The API is in a semi-stable state. This
means i'm trying not to break anything but i'm not yet in a place where i can
guarantee that it won't happen.

## API

[![GoDoc](https://godoc.org/github.com/spreadspace/telgo?status.svg)](https://godoc.org/github.com/spreadspace/telgo)
[Source code.](https://github.com/spreadspace/telgo)

## Licence

    © 2015 Christian Pointner <equinox@spreadspace.org>    3-clause BSD
