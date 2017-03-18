/*
 * Resource package
 * resource package implementation
 */
package resource

import "io"

// Type indicates a type of resource
type Type uint

const (
	Unknown Type = iota // not to be used
	File                // File if resource if a File
	Folder              // Folder if resource is a folder
)

/*
 * Package represents a container of resources (folders or binary/text files).
 */
type Package interface {

	// Open returns a resource.Item that represents the package root.
	Open(URI string) (Item, error)
}

/*
 * an Item is an element of a resource package, file or folder.
 */
type Item interface {

	// Open returns a ReadCloser on current item.
	Open() (io.ReadCloser, error)

	// Type returns the type of current file, file or folder
	Type() Type

	// Files returns a slice of the slice contained in current folder, or an
	// empty slice if current file is not a folder.
	Files() []Item
}
