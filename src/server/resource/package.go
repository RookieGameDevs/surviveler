/*
 * Resource package
 * resource package implementation
 */
package resource

import (
	"fmt"
	"io"
	"os"
	"path"
)

// Type indicates a type of resource
type Type uint

const (
	Unknown Type = iota // not to be used
	File                // File if resource if a File
	Folder              // Folder is resource if a folder
)

/*
 * Package represents a container of resources (folders or binary/text files).
 *
 * A package is the high level abstraction that represents the container, and a
 * way to read its content. The resources contained are accessed through their
 * URI, that is the relative path of the given resource, from the package root.
 */
type Package interface {

	// GetReader returns a reader of the resource at specified URI.
	//
	// Is is the caller's responsibility to close the reader if necessary.
	GetReader(URI string) (io.ReadCloser, error)

	// Exists checks if an uri exists inside the package.
	//
	// It returns a boolean indicating the existence of the specified URI and a
	// Type value indicating the resource type.
	Exists(URI string) (bool, Type)
}

/*
 * AssetsFolder is a simple filesystem folder.
 */
type AssetsFolder struct {
	root string // folder absolute path
}

// GetReader returns a reader of the resource at specified URI
//
// Is is the caller's responsibility to close the reader if necessary.
func (af AssetsFolder) GetReader(URI string) (io.ReadCloser, error) {
	if exists, _ := af.Exists(URI); !exists {
		return nil, fmt.Errorf("'%s' not found in assets folder '%s'", URI, af.root)
	}
	p := path.Join(af.root, URI)
	return os.Open(p)
}

/*
 * OpenAssetsFolder returns a new AssetsFolder, as a Package
 */
func OpenAssetsFolder(path string) Package {
	return AssetsFolder{root: path}
}

// Exists checks if an uri exists inside the package.
//
// It returns a boolean indicating the existence of the specified URI and a
// Type value indicating the resource type.
func (af AssetsFolder) Exists(URI string) (bool, Type) {
	p := path.Join(af.root, URI)
	nfo, err := os.Stat(p)
	if err == nil {
		if nfo.IsDir() {
			return true, Folder
		}
		return true, File
	}
	return false, Unknown
}
