/*
 * Surviveler resource package
 * surviveler resource package implementation
 */
package resource

import (
	"encoding/json"
	"fmt"
	"golang.org/x/image/bmp"
	"image"
	"io"
	"os"
	"path"
)

// URI of some static elements contained in a package
const (
	mapURI      string = "map/data.json"
	entitiesURI string = "entities/data.json"
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
 *
 * The specified URI must represent a file, not a directory
 */
func (sp SurvivelerPackage) Exists(uri string) bool {
	p := path.Join(sp.root, uri)
	fi, err := os.Stat(p)
	return err == nil && !fi.IsDir()
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
 * LoadJSON decodes a JSON resource, which location is specified by uri, into
 * an interface
 */
func (sp SurvivelerPackage) LoadJSON(uri string, i interface{}) error {
	if !sp.Exists(uri) {
		uri = uri + "/data.json"
	}
	r, err := sp.getReader(uri)
	if err != nil {
		return err
	}
	defer r.Close()
	decoder := json.NewDecoder(r)
	return decoder.Decode(i)
}

/*
 * LoadBitmap loads and a bitmap image contained in a package.
 */
func (sp SurvivelerPackage) LoadBitmap(uri string) (image.Image, error) {
	r, err := sp.getReader(uri)
	if err != nil {
		return nil, err
	}
	defer r.Close()
	return bmp.Decode(r)
}

/*
 * LoadMapData loads the map from the package and decodes it in a MapData
 * struct
 */
func (sp SurvivelerPackage) LoadMapData() (*MapData, error) {
	md := new(MapData)
	err := sp.LoadJSON(mapURI, &md)
	return md, err
}

/*
 * LoadEntitiesData loads the entities data from the package and decodes it in
 * a EntititesData struct
 */
func (sp SurvivelerPackage) LoadEntitiesData() (*EntitiesData, error) {
	md := new(EntitiesData)
	err := sp.LoadJSON(entitiesURI, &md)
	return md, err
}
