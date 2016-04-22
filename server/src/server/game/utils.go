package game

import (
	"log"
)

// FatalError logs a fatal error and exitd$ simply check
func FatalError(err error, ctx string) {

	if err != nil {
		log.Fatalf("Error (%s) %v\n", ctx, err.Error())
	}
}
