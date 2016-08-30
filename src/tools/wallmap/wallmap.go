package main

import (
	"flag"
	"fmt"
	"math"
	"os"

	"image/color"
	"image/png"

	"github.com/fogleman/gg"
)

var (
	scale   = flag.Int("scale", 1, "map mesh scale factor")
	pngfile = flag.String("png", "out.png", "output png file")
	dbg     = flag.Bool("v", false, "verbose output")
)

func showUsage() {
	fmt.Println("wallmap - Rasterize the triangular faces of an OBJ file onto a PNG image")
	fmt.Println()
	fmt.Println("usage:")
	fmt.Println("  wallmap -div INT -png FILE OBJFILE")
	flag.PrintDefaults()
}

func main() {

	objpath := ""
	flag.Parse()
	if flag.NArg() > 0 {
		objpath = flag.Arg(0)
	} else {
		showUsage()
		os.Exit(0)
	}

	obj, err := ReadObjFile(objpath, *dbg)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	if *dbg {
		fmt.Println("num vertices: ", len(obj.Vertices()))
		fmt.Println("num faces: ", len(obj.Triangles()))
		fmt.Println("scale factor: ", *scale)
	}

	// get image w/h by scaling the mesh aabb by the user-defined scale factor
	aabb := obj.AABB()
	aabb.Scale(float64(*scale))
	offx, offy := int(math.Floor(aabb.MinX)), int(math.Floor(aabb.MinZ))
	w, h := int(math.Ceil(aabb.MaxX)), int(math.Ceil(aabb.MaxZ))

	dc := gg.NewContext(w, h)
	dc.SetRGB255(255, 255, 255)
	dc.Clear()

	for _, t := range obj.Triangles() {
		// scale current triangle
		t.Scale(float64(*scale))

		// draw the triangle
		dc.MoveTo(t.P1.X(), t.P1.Z())
		dc.LineTo(t.P2.X(), t.P2.Z())
		dc.LineTo(t.P3.X(), t.P3.Z())
		dc.LineTo(t.P1.X(), t.P1.Z())
		dc.SetRGB255(0, 0, 0)
		dc.SetLineWidth(1)
		dc.FillPreserve()
		dc.Stroke()
	}
	fmt.Println("Rasterization completed")
	fmt.Println("Creating", *pngfile)

	f, err := os.Create(*pngfile)
	if err != nil {
		fmt.Println("Can't create ", *pngfile, ": ", err)
		os.Exit(1)
	}

	// convert image into a black and white one
	bw := []color.Color{color.Black, color.White}
	gr := &Converter{dc.Image(), color.Palette(bw)}

	err = png.Encode(f, gr)
	if err != nil {
		fmt.Println("Can't encode ", *pngfile, ": ", err)
		os.Exit(1)
	}

	fmt.Println("Resulting image details")

	if *dbg {
		fmt.Println("original mesh bounding box: ", obj.AABB())
		fmt.Println("scaled mesh bounding box: ", aabb)
	}
	fmt.Println("x, y offset: ", offx, offy)
	fmt.Println("scale: ", *scale)
	fmt.Println("width/height: ", w, h)
}
