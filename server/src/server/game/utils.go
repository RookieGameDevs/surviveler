/*
 * Surviveler game package
 * utility
 */
package game

import (
	"time"
)

/*
 * MakeTimestamp returns the current timestamp in milliseconds
 */
func MakeTimestamp() int64 {
	return time.Now().UnixNano() / int64(time.Millisecond)
}
