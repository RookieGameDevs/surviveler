/*
 * Surviveler resource package
 * resource package type and current implementation
 */
package resource

import (
	//log "github.com/Sirupsen/logrus"
	"fmt"
	"io"
	"os"
	"path"
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
func (rr SurvivelerPackage) Exists(uri string) bool {
	p := path.Join(rr.root, uri)
	_, err := os.Stat(p)
	return err == nil
}

/*
 * getReader obtains a ready to use reader, for the specified uri.
 *
 * It the responsibility of the caller to close the returned ReadCloser once
 * done
 */
func (rr SurvivelerPackage) getReader(uri string) (io.ReadCloser, error) {

	if !rr.Exists(uri) {
		return nil, fmt.Errorf("Resource not found: %s", uri)
	}
	p := path.Join(rr.root, uri)
	return os.Open(p)
}

func (rr SurvivelerPackage) MapReader() (io.ReadCloser, error) {
	return rr.getReader("map/data.json")
}
