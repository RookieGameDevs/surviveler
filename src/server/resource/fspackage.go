package resource

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path"
	"path/filepath"
	"strings"
)

// FSPackage implements the Package interface for loading of filesystem
// resources (simple folders and files).
type FSPackage struct {
	root FSItem
}

// OpenFSPackage opens a filesystem package, (i.e a folder).
func OpenFSPackage(rootURI string) (Package, error) {
	var (
		abs string
		err error
	)
	abs, err = filepath.Abs(rootURI)
	if err != nil {
		return nil, err
	}
	_, err = os.Stat(abs)
	if err != nil {
		return nil, err
	}
	return &FSPackage{
		root: FSItem{
			root: abs,
			cur:  ".",
		},
	}, nil
}

func isSlashRune(r rune) bool { return r == '/' || r == '\\' }

func startsWithDotDot(v string) bool {
	if !strings.Contains(v, "..") {
		return false
	}
	for _, ent := range strings.FieldsFunc(v, isSlashRune) {
		// we are only interested by the first field
		return ent == ".."
	}
	return false
}

// Open opens the directory at given URI and returns the root item.
func (fs FSPackage) Open(URI string) (Item, error) {
	var (
		abs string
		err error
	)
	// forge absolute file path from package root and given URI
	abs = path.Join(fs.root.root, URI)

	// check the requested URI is inside the package
	rel, err := filepath.Rel(fs.root.root, abs)
	if err != nil {
		return nil, fmt.Errorf("URI (%v) must be relative to package root (%v)", URI, fs.root.root)
	}
	if startsWithDotDot(rel) {
		return nil, fmt.Errorf("URI (%v) must contained in package root (%v)", URI, fs.root.root)
	}

	_, err = os.Stat(abs)
	if err != nil {
		return nil, err
	}
	return FSItem{root: fs.root.root, cur: URI}, nil
}

// A FSItem is a filesystem item, file or folder.
type FSItem struct {
	root string // package root absolute path
	cur  string // current element relative path from the root
}

// Type returns the type of current file, file or folder
func (fs FSItem) Type() Type {
	abs := path.Join(fs.root, fs.cur)
	nfo, err := os.Stat(abs)
	if err != nil {
		return unknown
	}
	mode := nfo.Mode()
	switch {
	case mode.IsDir():
		return Folder
	case mode.IsRegular():
		return File
	}
	return unknown
}

// Files returns a slice of the files contained in current item, or an
// empty slice if current item is not a folder.
func (fs FSItem) Files() []Item {
	items := []Item{}
	switch fs.Type() {
	case Folder:
		abs := path.Join(fs.root, fs.cur)
		files, _ := ioutil.ReadDir(abs)
		for _, f := range files {
			items = append(items, FSItem{root: abs, cur: f.Name()})
		}
	}
	return items
}

// Open returns a ReadCloser on item at URI.
//
// It returns an error if current item is not a file or is not readable.
func (fs FSItem) Open() (io.ReadCloser, error) {
	abs := path.Join(fs.root, fs.cur)
	switch fs.Type() {
	case File:
		f, err := os.Open(abs)
		if err != nil {
			return nil, err
		}
		return f, nil

	default:
		return nil, fmt.Errorf("can't read fspackage item %v", abs)
	}
}
