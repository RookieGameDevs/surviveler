/*
 * Surviveler resource package
 * surviveler resource package implementation
 */
package resource

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path"
)

const (
	mapUri string = "map/data.json"
)

/*
 * SurvivelerPackage represents a package of data, resource files and assets for
 * the game Surviveler, grouped into a package.

 * A package is a basic filesystem folder, a resource is a file in that folder,
 * and the resource uri is the path of this resource, relative to the package
 * root folder.
 */
type SurvivelerPackage struct {
	root string // package root folder path
}

/*
 * NewSurvivelerPackage opens the package at the specified path
 */
func NewSurvivelerPackage(path string) SurvivelerPackage {
	return SurvivelerPackage{root: path}
}

/*
 * Exists check if an uri exists inside a package
 */
func (sp SurvivelerPackage) Exists(uri string) bool {
	p := path.Join(sp.root, uri)
	_, err := os.Stat(p)
	return err == nil
}

/*
 * getReader obtains a ready to use reader, for the specified uri.
 *
 * It the responsibility of the caller to close the returned ReadCloser once
 * done
 */
func (sp SurvivelerPackage) getReader(uri string) (io.ReadCloser, error) {
	if !sp.Exists(uri) {
		return nil, fmt.Errorf("Resource not found: %s", uri)
	}
	p := path.Join(sp.root, uri)
	return os.Open(p)
}

/*
 * loadJSON decodes a JSON resource, which location is specified by uri, into
 * an interface
 */
func (sp SurvivelerPackage) loadJSON(uri string, i interface{}) error {
	r, err := sp.getReader(uri)
	if err != nil {
		return err
	}
	defer r.Close()
	decoder := json.NewDecoder(r)
	return decoder.Decode(i)
}

func (sp SurvivelerPackage) LoadMap(i interface{}) error {
	return sp.loadJSON(mapUri, i)
}
