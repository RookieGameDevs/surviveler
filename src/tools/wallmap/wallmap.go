package main

import (
	"flag"
	"fmt"
	"math"
	"os"

	"github.com/fogleman/gg"
	"golang.org/x/image/bmp"
)

var (
	scale   = flag.Int("scale", 1, "map mesh scale factor")
	bmpfile = flag.String("bmp", "out.bmp", "output bmp file")
	dbg     = flag.Bool("v", false, "verbose output")
)

func showUsage() {
	fmt.Println("wallmap - Rasterize a 'walls-only 3D map' onto a bitmap")
	fmt.Println()
	fmt.Println("usage:")
	fmt.Println("  wallmap -div INT -bmp FILE OBJFILE")
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
		fmt.Println("num triangles[0]: ", len(obj.Triangles))
		fmt.Println("triangles[0]: ", obj.Triangles[0])
		fmt.Println("scale factor: ", *scale)
		fmt.Println("org min: ", obj.MinX, obj.MinX)
		fmt.Println("org max: ", obj.MaxX, obj.MaxY)
	}

	// image width, height
	sMinX, sMaxX := float64(*scale)*obj.MinX, float64(*scale)*obj.MaxX
	sMinY, sMaxY := float64(*scale)*obj.MinY, float64(*scale)*obj.MaxY
	w, h := int(math.Ceil(sMaxX)), int(math.Ceil(sMaxY))

	if *dbg {
		fmt.Println("scale min: ", sMinX, sMinY)
		fmt.Println("scale max: ", sMaxX, sMaxY)
		fmt.Println("image width/height: ", w, h)
	}

	dc := gg.NewContext(w, h)
	dc.SetRGB(1, 1, 1)
	dc.Clear()

	for _, t := range obj.Triangles {
		// scale current triangle
		t.Scale(float64(*scale))

		// draw the triangle
		dc.MoveTo(t.P1.X(), t.P1.Y())
		dc.LineTo(t.P2.X(), t.P2.Y())
		dc.LineTo(t.P3.X(), t.P3.Y())
		dc.LineTo(t.P1.X(), t.P1.Y())
		dc.SetRGB(0, 0, 0)
		dc.SetLineWidth(1)
		dc.FillPreserve()
		dc.Stroke()
	}
	fmt.Println("Rasterization completed")
	fmt.Println("Creating", *bmpfile)

	f, err := os.Create(*bmpfile)
	if err != nil {
		fmt.Println("Can't create ", *bmpfile, ": ", err)
		os.Exit(1)
	}
	err = bmp.Encode(f, dc.Image())
	if err != nil {
		fmt.Println("Can't encode ", *bmpfile, ": ", err)
		os.Exit(1)
	}
}
