package main

import (
	"image"
	"image/color"
)

// Converter converts the original image with different color model.
//
// It implements image.Image as it contains the original image
type Converter struct {
	Img image.Image
	Mod color.Model
}

// ColorModel returns the color model
func (c *Converter) ColorModel() color.Model {
	// return the new color model...
	return c.Mod
}

// Bounds returns the original image bounds
func (c *Converter) Bounds() image.Rectangle {
	// ... but the original bounds
	return c.Img.Bounds()
}

// At forwards the call to the original image and then asks the color model to
// convert it.
func (c *Converter) At(x, y int) color.Color {
	return c.Mod.Convert(c.Img.At(x, y))
}
