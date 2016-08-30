// Copyright 2016 Aurélien Rainone. All rights reserved.
// Use of this source code is governed by MIT license.
// license that can be found in the LICENSE file.
//
// Part of this code has been inspired from golang/image/math/f32

package gogeo

import (
	"math"
)

// Epsilon is some tiny value that determines how precisely equal we want our floats to be
// This is exported and left as a variable in case you want to change the default threshold for the
// purposes of certain methods (e.g. Unproject uses the default epsilon when determining
// if the determinant is "close enough" to zero to mean there's no inverse).
//
// This is, obviously, not mutex protected so be **absolutely sure** that no functions using Epsilon
// are being executed when you change this.
var Epsilon = 1e-10

// FloatEqual is a safe utility function to compare floats.
// It's Taken from http://floating-point-gui.de/errors/comparison/
//
// It is slightly altered to not call Abs when not needed.
func FloatEqual(a, b float64) bool {
	return FloatEqualThreshold(a, b, Epsilon)
}

// FloatEqualFunc is a utility closure that will generate a function that
// always approximately compares floats like FloatEqualThreshold with a different
// threshold.
func FloatEqualFunc(epsilon float64) func(float64, float64) bool {
	return func(a, b float64) bool {
		return FloatEqualThreshold(a, b, epsilon)
	}
}

var (
	// MinNormal is the minimum positive normal 1 / 2**(127 - 1)
	MinNormal = 1.1754943508222875e-38
	// MinValue is next smallest float after 0
	MinValue = math.SmallestNonzeroFloat64
	// MaxValue is the maximal value representable with a float64
	MaxValue = math.MaxFloat64

	// InfPos represents the positive infinity
	InfPos = math.Inf(1)
	// InfNeg represents the negative infinity
	InfNeg = math.Inf(-1)
	// NaN represents a not-a-number
	NaN = math.NaN()
)

// FloatEqualThreshold is a utility function to compare floats.
// It's Taken from http://floating-point-gui.de/errors/comparison/
//
// It is slightly altered to not call Abs when not needed.
//
// This differs from FloatEqual in that it lets you pass in your comparison threshold, so that you can adjust the comparison value to your specific needs
func FloatEqualThreshold(a, b, epsilon float64) bool {
	if a == b { // Handles the case of inf or shortcuts the loop when no significant error has accumulated
		return true
	}

	diff := math.Abs(a - b)

	if a == 0 || b == 0 || diff < MinNormal { // If a or b are 0 or both are extremely close to it
		return diff < epsilon*MinNormal
	}
	// Else compare difference
	absA, absB := math.Abs(a), math.Abs(b)
	return diff/math.Min((absA+absB), MaxValue) < epsilon
}

// Clamp takes in a value and two thresholds. If the value is smaller than the low
// threshold, it returns the low threshold. If it's bigger than the high threshold
// it returns the high threshold. Otherwise it returns the value.
//
// Useful to prevent some functions from freaking out because a value was
// teeeeechnically out of range.
func Clamp(a, low, high float64) float64 {
	if a < low {
		return low
	} else if a > high {
		return high
	}

	return a
}

// ClampFunc generates a closure that returns its parameter
// clamped to the range [low,high].
func ClampFunc(low, high float64) func(float64) float64 {
	return func(a float64) float64 {
		return Clamp(a, low, high)
	}
}

// IsClamped uses strict equality (meaning: not the FloatEqual function) there
// shouldn't be any major issues with this since clamp is often used to fix minor
//i errors
//
// Checks if a is clamped between low and high as if
// Clamp(a, low, high) had been called.
// In most cases it's probably better to just call Clamp
// without checking this since it's relatively cheap.
func IsClamped(a, low, high float64) bool {
	return a >= low && a <= high
}

// SetMin checks if a > b, then a will be set to the value of b.
func SetMin(a *float64, b float64) {
	if b < *a {
		*a = b
	}
}

// SetMax checks if a < b, then a will be set to the value of b.
func SetMax(a *float64, b float64) {
	if *a < b {
		*a = b
	}
}

// Round shortens a float64 value to a specified precision (number of digits after the decimal point)
// with "round half up" tie-braking rule. Half-way values (23.5) are always rounded up (24).
func Round(v float64, precision int) float64 {
	p := float64(precision)
	t := float64(v) * math.Pow(10, p)
	if t > 0 {
		return float64(math.Floor(t+0.5) / math.Pow(10, p))
	}
	return float64(math.Ceil(t-0.5) / math.Pow(10, p))
}
