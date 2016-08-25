package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
)

type Vertex [4]float64

func (v *Vertex) Scale(f float64) {
	for i := range v {
		v[i] *= f
	}
}

func (v Vertex) X() float64 {
	return v[0]
}

func (v Vertex) Y() float64 {
	return v[1]
}

func (v Vertex) Z() float64 {
	return v[2]
}

func (v Vertex) W() float64 {
	return v[3]
}

func (v *Vertex) Set(s []string) error {
	var (
		err error
	)

	for i := range s {
		if v[i], err = strconv.ParseFloat(s[i], 64); err != nil {
			return fmt.Errorf("invalid syntax \"%v\": %s", s[i], err)
		}
	}

	return nil
}

// Triangle represents a 3-sided polygon
//
// NOTE: this could easily be extended to support N-sided polygons
// by using a []Vertex instead
type Triangle struct {
	P1, P2, P3 Vertex
}

func (t *Triangle) Scale(f float64) {
	t.P1.Scale(f)
	t.P2.Scale(f)
	t.P3.Scale(f)
}

type AABB struct {
	MinX, MaxX float64
	MinY, MaxY float64
	MinZ, MaxZ float64
}

// NewAABB initializes the bounding box.
//
// The bouding box will be valid after the first call to extend.
func NewAABB() AABB {
	return AABB{
		MinX: math.MaxFloat64,
		MinY: math.MaxFloat64,
		MinZ: math.MaxFloat64,
		MaxX: -math.MaxFloat64,
		MaxY: -math.MaxFloat64,
		MaxZ: -math.MaxFloat64,
	}
}

func (bb *AABB) extend(other AABB) {
	// update the min and max for each coord
	updateMin(&bb.MinX, other.MinX)
	updateMin(&bb.MinY, other.MinY)
	updateMin(&bb.MinZ, other.MinZ)
	updateMax(&bb.MaxX, other.MaxX)
	updateMax(&bb.MaxY, other.MaxY)
	updateMax(&bb.MaxZ, other.MaxZ)
}

func (bb *AABB) Scale(f float64) {
	bb.MinX *= f
	bb.MinY *= f
	bb.MinZ *= f
	bb.MaxX *= f
	bb.MaxY *= f
	bb.MaxZ *= f
}

// AABB computes and returns the axis-aligned bounding-box
// of the triangle.
func (t Triangle) AABB() AABB {
	return AABB{
		MinX: math.Min(t.P1.X(), math.Min(t.P2.X(), t.P3.X())),
		MinY: math.Min(t.P1.Y(), math.Min(t.P2.Y(), t.P3.Y())),
		MinZ: math.Min(t.P1.Z(), math.Min(t.P2.Z(), t.P3.Z())),
		MaxX: math.Max(t.P1.X(), math.Max(t.P2.X(), t.P3.X())),
		MaxY: math.Max(t.P1.Y(), math.Max(t.P2.Y(), t.P3.Y())),
		MaxZ: math.Max(t.P1.Z(), math.Max(t.P2.Z(), t.P3.Z())),
	}
}

func (t Triangle) isDegenerate() bool {
	// find the determinant of the 3x3 matrix in which the triangle coords can
	// be represented, it's 0 or close to 0.0, the triangle area is null and we
	// consider the triangle as degenerate
	det := (t.P1.X() * t.P2.Y() * t.P3.Z()) +
		(t.P1.Y() * t.P2.Z() * t.P3.X()) +
		(t.P1.Z() * t.P2.X() * t.P3.Y()) -
		(t.P1.Z() * t.P2.Y() * t.P3.X()) -
		(t.P1.Y() * t.P2.X() * t.P3.Z()) -
		(t.P1.X() * t.P2.Z() * t.P3.Y())

	// TODO: also check area with an epsilon?
	return det == 0.0
}

type ObjFile struct {
	vertices  []Vertex
	triangles []Triangle
	aabb      AABB
	dbg       bool
}

func (of ObjFile) Vertices() []Vertex {
	return of.vertices
}

func (of ObjFile) Triangles() []Triangle {
	return of.triangles
}

func (of ObjFile) AABB() AABB {
	return of.aabb
}

// updateMin checks if a > b, then a will be set to the value of b.
func updateMin(a *float64, b float64) {
	if b < *a {
		*a = b
	}
}

// updateMax checks if a < b, then a will be set to the value of b.
func updateMax(a *float64, b float64) {
	if *a < b {
		*a = b
	}
}

func (of *ObjFile) parseVertex(lineno int, kw string, data []string) error {
	v := Vertex{}
	err := v.Set(data)
	if err != nil {
		return err
	}
	// discard the Z coordinate
	of.vertices = append(of.vertices, v)
	return nil
}

func (of *ObjFile) parseFace(lineno int, kw string, data []string) error {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Error in parseFace", r)
			fmt.Printf("lineno: %+v | kw: +%v | data : %+v\n", lineno, kw, data)
			fmt.Println("len(of.vertices): ", len(of.vertices))
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
		P1: of.vertices[vi[0]-1],
		P2: of.vertices[vi[1]-1],
		P3: of.vertices[vi[2]-1],
	}

	// extend the mesh bounding box with the triangle
	of.aabb.extend(t.AABB())

	// discard degenerate triangles
	if t.isDegenerate() {
		if of.dbg {
			fmt.Println("found degenerate triangle: ", t)
		}
		return nil
	}

	of.triangles = append(of.triangles, t)
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
		aabb: NewAABB(),
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
