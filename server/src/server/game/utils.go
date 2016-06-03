/*
 * Surviveler game package
 * utility
 */
package game

import (
	"fmt"
	"time"
)

/*
 * MakeTimestamp returns the current timestamp in milliseconds
 */
func MakeTimestamp() int64 {
	return time.Now().UnixNano() / int64(time.Millisecond)
}

/*
 * uint32Value is an explicit 32 bits unsigned type.
 *
 * It implements the flag.Value interface
 */
type uint32Value uint32

func (i *uint32Value) String() string {
	return fmt.Sprintf("%v", *i)
}

func (i *uint32Value) Set(s string) error {
	if _, err := fmt.Sscanf(s, "%d", i); err != nil {
		return fmt.Errorf("invalid syntax \"%s\"", s)
	}
	return nil
}
