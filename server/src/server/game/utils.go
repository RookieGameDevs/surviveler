package game

import (
	"log"
	"time"
)

// FatalError logs a fatal error and exits
func FatalError(err error, ctx string) {

	if err != nil {
		log.Fatalf("Error (%s) %v\n", ctx, err.Error())
	}
}

// MakeTimestamp returns the current timestamp in milliseconds
func MakeTimestamp() int64 {
	return time.Now().UnixNano() / int64(time.Millisecond)
}
