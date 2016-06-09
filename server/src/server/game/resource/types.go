/*
 * Surviveler resource package
 * resource package data types
 */
package resource

import (
	"server/math"
)

type Rect2D [2]math.Vec2

type MapObject struct {
	Ref      string    `json:"ref"`      // uri of the object inside the package
	Pos      math.Vec2 `json:"pos"`      // position of the object on the map
	Rotation int       `json:"rotation"` // rotation of the object on the map
}

type ResourceList map[string]string

/*
 * Spawn regroups the spawn points for different kinds of entities
 */
type Spawn struct {
	Player  math.Vec2   `json:"player"`  // player unique spawn point
	Enemies []math.Vec2 `json:"enemies"` // list of spawn points for enemies
}

/*
 * MapData regroups settings and information about the map
 */
type MapData struct {
	Resources   ResourceList `json:"resources"`
	ScaleFactor float32      `json:"scale_factor"`
	Objects     []MapObject  `json:"objects"`
	Spawn       Spawn        `json:"spawn"`
}
