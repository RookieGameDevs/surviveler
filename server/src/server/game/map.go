/*
 * Surviveler game package
 * map representation
 */
package game

import (
	"server/game/resource"
)

type Map struct{}

/*
 * LoadFrom initializes a map from a SurvivelerPackage
 */
func (m *Map) LoadFrom(pkg resource.SurvivelerPackage) error {

	r, err := pkg.GetReader(resource.MapUri)
	if err != nil {
		return err
	}
	defer r.Close()
	return nil
}
