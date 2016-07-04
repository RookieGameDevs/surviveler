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
	Players VecList `json:"players"` // player unique spawn point
	Enemies VecList `json:"enemies"` // list of spawn points for enemies
}

/*
 * AIKeypoints regroups the various AI-related key points on the map
 */
type AIKeypoints struct {
	Spawn Spawn `json:"spawn"` // entity spawn points
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

/*
 * EntityDAta regroups settings and information about the specific entity type.
 */
type EntityData struct {
	Resources     ResourceList `json:"resources"`
	BuildingPower uint8        `json:"building_power"`
	Speed         uint8        `json:"speed"`
}

/*
 * BuildingData regroups settings and information about the specific buildnig
 * type.
 */
type BuildingData struct {
	Resources        ResourceList `json:"resources"`
	TotHp            uint16       `json:"tot_hp"`
	BuildingPowerRec uint16       `json:"building_power_req"`
}
