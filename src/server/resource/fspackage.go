package resource

import (
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path"
	"path/filepath"
)

type FSPackage struct {
	root FSItem
}

// OpenFSPackage opens a filesystem package, that is, a folder.
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

func (fs FSPackage) Open(URI string) (Item, error) {
	var (
		abs string
		err error
	)
	// forge absolute file path from package root and given URI
	abs = path.Join(fs.root.root, URI)
	_, err = os.Stat(abs)
	if err != nil {
		return nil, err
	}
	return FSItem{root: fs.root.root, cur: URI}, nil
}

type FSItem struct {
	root string // package root absolute path
	cur  string // current element relative path from the root
}

func (fs FSItem) Type() Type {
	abs := path.Join(fs.root, fs.cur)
	nfo, err := os.Stat(abs)
	if err != nil {
		return Unknown
	}
	mode := nfo.Mode()
	switch {
	case mode.IsDir():
		return Folder
	case mode.IsRegular():
		return File
	}
	return Unknown
}

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

func (fs FSItem) Open() (io.ReadCloser, error) {
	abs := path.Join(fs.root, fs.cur)
	switch fs.Type() {
	case File:
		if f, err := os.Open(abs); err != nil {
			return nil, err
		} else {
			return f, nil
		}
	default:
		return nil, fmt.Errorf("can't open package item %v for reading", abs)
	}
}
