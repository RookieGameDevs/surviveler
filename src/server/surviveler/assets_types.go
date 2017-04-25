/*
 * Surviveler package
 * game data: types definitions
 */
package surviveler

import "github.com/aurelien-rainone/gogeo/f32/d2"

type Rect2D [2]d2.Vec2
type VecList []d2.Vec2

// gameData is the top-level struct containing game data
type gameData struct {
	world         *World
	mapData       *MapData
	buildingsData BuildingDataDict
	entitiesData  EntityDataDict
}

type (
	BuildingDataDict map[EntityType]*BuildingData
	EntityDataDict   map[EntityType]*EntityData
)

type MapObject struct {
	Ref      string  `json:"ref"`            // uri of the object inside the package
	Pos      d2.Vec2 `json:"pos"`            // position of the object on the map
	Rotation int     `json:"rotation"`       // rotation of the object on the map
	Note     string  `json:"note,omitEmpty"` // note on the object
	// TODO: remove the omitEmpty
	BoundingBox2D d2.Vec2 `json:"bounding_box_2d,omitEmpty"` // 2d bounding box
}

type MapUsableObject struct {
	MapObject
	Type uint8 `json:"type"`
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
	Resources     ResourceList      `json:"resources"`
	ScaleFactor   float32           `json:"scale_factor"`
	UsableObjects []MapUsableObject `json:"usable_objects"`
	Objects       []MapObject       `json:"objects"`
	AIKeypoints   AIKeypoints       `json:"ai_keypoints"`
}

/*
 * EntititesData lists the URI for the various entity types
 */
type EntitiesData struct {
	Entities  map[string]string `json:"entities_map"`
	Buildings map[string]string `json:"buildings_map"`
}

/*
 * EntityData regroups settings and information about a specific player entity
 * type
 */
type EntityData struct {
	BuildingPower uint8   `json:"building_power"`
	CombatPower   uint8   `json:"combat_power"`
	TotalHP       uint16  `json:"tot_hp"`
	Speed         float32 `json:"speed"`
}

/*
 * BuildingData regroups settings and information about a specific building
 * entity type
 */
type BuildingData struct {
	TotHp            uint16 `json:"tot_hp"`
	BuildingPowerRec uint16 `json:"building_power_req"`
}
