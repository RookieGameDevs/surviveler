package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strings"
)

type Point2 struct {
	X, Y float64
}

func (p *Point2) Scale(f float64) {
	p.X = p.X * f
	p.Y = p.Y * f
}

func Point2From3(p Point3) Point2 {
	return Point2{p.X, p.Y}
}

type Point3 struct {
	X, Y, Z float64
}

func (p *Point3) Set(s []string) error {
	if _, err := fmt.Sscanf(s[0], "%f", &p.X); err != nil {
		return fmt.Errorf("invalid syntax \"%s\"", s)
	}
	if _, err := fmt.Sscanf(s[1], "%f", &p.Z); err != nil {
		return fmt.Errorf("invalid syntax \"%s\"", s)
	}
	if _, err := fmt.Sscanf(s[2], "%f", &p.Y); err != nil {
		return fmt.Errorf("invalid syntax \"%s\"", s)
	}
	return nil
}

type Triangle struct {
	P1, P2, P3 Point2
}

func (t *Triangle) Scale(f float64) {
	t.P1.Scale(f)
	t.P2.Scale(f)
	t.P3.Scale(f)
}

func (t Triangle) MinX() float64 {
	return math.Min(t.P1.X, math.Min(t.P2.X, t.P3.X))
}

func (t Triangle) MinY() float64 {
	return math.Min(t.P1.Y, math.Min(t.P2.Y, t.P3.Y))
}

func (t Triangle) MaxX() float64 {
	return math.Max(t.P1.X, math.Max(t.P2.X, t.P3.X))
}

func (t Triangle) MaxY() float64 {
	return math.Max(t.P1.Y, math.Max(t.P2.Y, t.P3.Y))
}

func (t Triangle) isDegenerate() bool {
	area := ((t.P2.X-t.P1.X)*(t.P3.Y-t.P1.Y) -
		(t.P3.X-t.P1.X)*(t.P2.Y-t.P1.Y))
	// TODO: also check area with an epsilon?
	return area == 0.0
}

type ObjFile struct {
	Vertices               []Point2
	Triangles              []Triangle
	MinX, MinY, MaxX, MaxY float64
	dbg                    bool
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

func (of *ObjFile) parseVertex(lineno int, kw string, data []string) error {
	p3 := Point3{}
	err := p3.Set(data)
	if err != nil {
		return err
	}
	// discard the Z coordinate
	of.Vertices = append(of.Vertices, Point2From3(p3))
	return nil
}

func (of *ObjFile) parseFace(lineno int, kw string, data []string) error {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Error in parseFace", r)
			fmt.Printf("lineno: %+v | kw: +%v | data : %+v\n", lineno, kw, data)
			fmt.Println("len(of.Vertices): ", len(of.Vertices))
			os.Exit(1)
		}
	}()

	if len(data) != 3 {
		return fmt.Errorf("line: %d, only triangular faces are supported", lineno)
	}

	// vertices indices
	vi := [3]int{}
	for i, s := range data {
		// we are only interested in the vertex index
		sidx := strings.Split(s, "/")[0]
		if _, err := fmt.Sscanf(sidx, "%d", &(vi[i])); err != nil {
			return fmt.Errorf("invalid syntax \"%s\"", s)
		}
	}

	t := Triangle{
		P1: of.Vertices[vi[0]-1],
		P2: of.Vertices[vi[1]-1],
		P3: of.Vertices[vi[2]-1],
	}

	// track min/max bounds
	SetMin(&of.MinX, t.MinX())
	SetMin(&of.MinY, t.MinY())
	SetMax(&of.MaxX, t.MaxX())
	SetMax(&of.MaxY, t.MaxY())

	// discard degenerate triangles
	if t.isDegenerate() {
		if of.dbg {
			fmt.Println("found degenerate triangle: ", t)
		}
		return nil
	}

	of.Triangles = append(of.Triangles, t)
	return nil
}

func ReadObjFile(path string, dbg bool) (*ObjFile, error) {
	in, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer in.Close()

	lineno := 0

	// init min/max values
	obj := ObjFile{
		MinX: math.MaxFloat64,
		MinY: math.MaxFloat64,
		MaxX: -math.MaxFloat64,
		MaxY: -math.MaxFloat64,
		dbg:  dbg,
	}

	scanner := bufio.NewScanner(in)
	for scanner.Scan() {
		line := strings.Split(scanner.Text(), " ")
		kw, vals := line[0], line[1:]
		switch kw {
		case "v":
			err := obj.parseVertex(lineno, kw, vals)
			if err != nil {
				return nil, fmt.Errorf("error parsing vertex: %v", err)
			}
		case "f":
			err := obj.parseFace(lineno, kw, vals)
			if err != nil {
				return nil, fmt.Errorf("error parsing face: %v", err)
			}
		default:
			// ignore everything else
		}

		lineno++
	}
	return &obj, nil
}
