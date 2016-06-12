/*
 * Surviveler resource package
 * resource package data types
 */
package resource

import (
	"server/math"
)

type Rect2D [2]math.Vec2
type VecList []math.Vec2

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
	Player  math.Vec2 `json:"player"`  // player unique spawn point
	Enemies VecList   `json:"enemies"` // list of spawn points for enemies
}

/*
 * AIKeypoints regroups the various AI-related key points on the map
 */
type AIKeypoints struct {
	Spawn         Spawn   // entity spawn points
	WanderingDest VecList // list of destination chosen randomly for wanderers
}

/*
 * MapData regroups settings and information about the map
 */
type MapData struct {
	Resources   ResourceList `json:"resources"`
	ScaleFactor float64      `json:"scale_factor"`
	Objects     []MapObject  `json:"objects"`
	AIKeypoints AIKeypoints  `json:"ai_keypoints"`
}
