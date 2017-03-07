/*
 * Resource package
 * resource loaders
 */
package resource

import (
	"encoding/json"
	"fmt"
	"io"
)

// LoadJSON decodes a JSON file coming from pkg into interface i
func LoadJSON(pkg Package, URI string, i interface{}) error {
	fmt.Println("LoadJSON from pkg", pkg.(*FSPackage).root, "URI: ", URI)
	item, err := pkg.Open(URI)
	fmt.Println("item ", item)
	if err != nil {
		return err
	}
	var f io.ReadCloser
	f, err = item.Open()
	if err != nil {
		return err
	}
	defer f.Close()
	decoder := json.NewDecoder(f)
	err = decoder.Decode(&i)
	return err
}
