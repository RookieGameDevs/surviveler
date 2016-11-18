package surviveler

import "github.com/aurelien-rainone/gogeo/f32/d2"

// VecStack represents a stack of d2.Vec2.
type VecStack struct {
	top  *item
	size int
}

// internal item structure.
type item struct {
	value d2.Vec2
	next  *item
}

// newVecStack initializes and returns a new stack of d2.Vec2.
func newVecStack() *VecStack {
	return &VecStack{}
}

// Len returns the stack's length.
func (s *VecStack) Len() int {
	return s.size
}

// Push pushes a new item on top of the stack.
func (s *VecStack) Push(value d2.Vec2) {
	s.top = &item{value, s.top}
	s.size++
}

// Pop removes the topmost item from the stack and return its value.
//
// If the stack is empty, Pop returns nil.
func (s *VecStack) Pop() (value d2.Vec2) {
	if s.size > 0 {
		value, s.top = s.top.value, s.top.next
		s.size--
		return
	}
	return nil
}

// PopLast removes the bottommost item.
//
// PopLast does nothing if the stack does not contain at least 2 items.
func (s *VecStack) PopLast() (value d2.Vec2) {
	if lastElem := s.popLast(s.top); s.size >= 2 && lastElem != nil {
		return lastElem.value
	}
	return nil
}

// Peek returns the topmost item without removing it from the stack.
func (s *VecStack) Peek() (value d2.Vec2, exists bool) {
	exists = false
	if s.size > 0 {
		value = s.top.value
		exists = true
	}
	return
}

// PeekN returns at max the N topmost item without removing them from the stack.
func (s *VecStack) PeekN(n int) []d2.Vec2 {
	var (
		N   []*d2.Vec2
		cur *item
	)
	N = make([]d2.Vec2, 0, n)
	cur = s.top
	for len(N) < n {
		if cur == nil {
			break
		}
		N = append(N, cur.value)
		cur = cur.next
	}
	return N
}

func (s *VecStack) popLast(elem *item) *item {
	if elem == nil {
		return nil
	}
	// not last because it has next and a grandchild
	if elem.next != nil && elem.next.next != nil {
		return s.popLast(elem.next)
	}

	// current elem is second from bottom, as next elem has no child
	if elem.next != nil && elem.next.next == nil {
		last := elem.next
		// make current elem bottom of stack by removing its next item
		elem.next = nil
		s.size--
		return last
	}
	return nil
}
