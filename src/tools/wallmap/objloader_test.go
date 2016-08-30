package main

import "testing"

func TestDegenerateTriangle(t *testing.T) {
	var degTests = []struct {
		x1, y1, z1 float64
		x2, y2, z2 float64
		x3, y3, z3 float64
		expected   bool
	}{
		// 3 same points
		{0, 0, 0, 0, 0, 0, 0, 0, 0, true},
		{0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, true},
		{0.353567426756, 0.353567426756, 0.353567426756, 0.353567426756, 0.353567426756, 0.353567426756, 0.353567426756, 0.353567426756, 0.353567426756, true},
		{1, 1, 1, 1, 1, 1, 1, 1, 1, true},

		// 2 same points
		{1, 0, 0, 0, 0, 0, 0, 0, 0, true},
		{0, 1, 0, 0, 0, 0, 0, 0, 0, true},
		{0, 0, 1, 0, 0, 0, 0, 0, 0, true},
		{0, 0, 0, 1, 0, 0, 0, 0, 0, true},
		{0, 0, 0, 0, 1, 0, 0, 0, 0, true},
		{0, 0, 0, 0, 0, 1, 0, 0, 0, true},
		{0, 0, 0, 0, 0, 0, 1, 0, 0, true},
		{0, 0, 0, 0, 0, 0, 0, 1, 0, true},
		{0, 0, 0, 0, 0, 0, 0, 0, 1, true},

		// 3 points on same line (axis //)
		{1, 0, 0, 2, 0, 0, 3, 0, 0, true},
		{0, 1, 0, 0, 2, 0, 0, 3, 0, true},

		// 3 points on same line (random)
		{0, 0, 0, 1, 2, 3, 2, 4, 6, true},
		{-0.5, 1.5, 1, 1, 2, 3, 2.5, 2.5, 5, true},
		{1 / 3, -1 / 6, 1 / 12, -1, 1 / 2, -2, -1 / 3, 1 / 6, -25/24 + 1/12, true},

		// very small area
		{1, 0, 0, 0, 1, 0, 0, 0, 0.000001, true},

		// not degenerate
		{1, 2, 3, -4, 5, 6, 7, 8, -9, false},
		{1, 1, 2, 1, 2, 0, 2, 1, 0, false},
	}

	for _, tt := range degTests {
		triangle := Triangle{
			P1: NewVertex3D(tt.x1, tt.y1, tt.z1),
			P2: NewVertex3D(tt.x2, tt.y2, tt.z2),
			P3: NewVertex3D(tt.x3, tt.y3, tt.z3),
		}
		actual := triangle.isDegenerate()
		if actual != tt.expected {
			t.Errorf("Triangle.isDegenerate() (%v): expected %v, actual %v", triangle, tt.expected, actual)
		}
	}
}
