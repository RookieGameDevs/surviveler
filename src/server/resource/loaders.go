/*
 * Resource package
 * resource loaders
 */
package resource

import (
	"encoding/json"
	"image"

	"golang.org/x/image/bmp"
)

/*
 * LoadJSON decodes a JSON resource inside a Package into an interface
 */
func LoadJSON(pkg Package, URI string, i interface{}) error {
	exists, t := pkg.Exists(URI)
	if exists && t == Folder {
		URI = URI + "/data.json"
	}
	r, err := pkg.GetReader(URI)
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
func LoadBitmap(pkg Package, URI string) (image.Image, error) {
	r, err := pkg.GetReader(URI)
	if err != nil {
		return nil, err
	}
	defer r.Close()
	return bmp.Decode(r)
}
