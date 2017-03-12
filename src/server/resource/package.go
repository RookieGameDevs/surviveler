// Package resource proposes interfaces and types for the loading of resource files
package resource

import "io"

// Type indicates a type of resource
type Type uint

const (
	unknown Type = iota
	// File if resource if a File
	File
	// Directory if resource is a container of resource.Items.
	Directory
)

// A Package represents a container of resources (directories or binary/text files).
type Package interface {

	// Open opens the package at given URI and returns the root item.
	Open(URI string) (Item, error)
}

// An Item is an element of a resource package, file or directory.
type Item interface {

	// Open returns a ReadCloser on item at URI.
	//
	// It returns an error if current item is not a file or is not readable.
	Open() (io.ReadCloser, error)

	// Type returns the type of current file, file or directory.
	Type() Type

	// Files returns a slice of the items contained in current folder, or an
	// empty slice if current file is not a folder.
	Files() []Item
}
