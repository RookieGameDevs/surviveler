// Package resource proposes interfaces and types for the loading of resource files
package resource

import "io"

// Type indicates a type of resource
type Type uint

const (
	unknown Type = iota
	// File if resource if a File
	File
	// Folder if resource is a folder
	Folder
)

// A Package represents a container of resources (folders or binary/text files).
type Package interface {

	// Open opens the package at given URI and returns the root item.
	Open(URI string) (Item, error)
}

// An Item is an element of a resource package, file or folder.
type Item interface {

	// Open returns a ReadCloser on item at URI.
	//
	// It returns an error if current item is not a file or is not readable.
	Open() (io.ReadCloser, error)

	// Type returns the type of current file, file or folder
	Type() Type

	// Files returns a slice of the files contained in current item, or an
	// empty slice if current item is not a folder.
	Files() []Item
}
