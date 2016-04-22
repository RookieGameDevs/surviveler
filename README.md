Surviveler. The award winning game. Probably.

# Project structure

It will really speed up the Golang dev workflow while basically not impacting
the client one, if we have our game root dir living inside a standard Golang
folder structure. So, once the $GOPATH is defined:

```
cd $GOPATH
git clone git@bitbucket.org:rookiegamedevs/surviveler.git $GOPATH/src/bitbucket.com/rookiegamedevs/surviveler
```

## Alternative solution

Also, in case you don't want to have the project clone inside a Go folder
structure, you can just symlink the project root dir in another Go directory
structure, anywhere on your system.
To build the server executable, as you will need the structure described
before, you can make Go *believe* the project resides at
`$GOPATH/src/bitbucket.com/rookiegamedevs/surviveler` by symlink the project
root with that specific folder.
