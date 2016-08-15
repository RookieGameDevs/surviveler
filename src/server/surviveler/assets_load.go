/*
 * Surviveler package
 * game data: loading from assets
 */
package surviveler

import (
	"errors"
	"fmt"
	"image"
	"server/game"
	"server/resource"

	log "github.com/Sirupsen/logrus"
)

// URI of some static elements contained in a package
const (
	mapURI      string = "map/data.json"
	entitiesURI string = "entities/data.json"
)

// TODO: this map is hard-coded for now, but will be read from resources
// in the future
var _entityTypes = map[string]game.EntityType{}

/*
 * LoadMapData loads the map data from the given package.
 *
 * It decodes it into a MapData struct
 */
func LoadMapData(pkg resource.SurvivelerPackage) (*MapData, error) {
	md := new(MapData)
	err := pkg.LoadJSON(mapURI, &md)
	return md, err
}

/*
 * LoadEntitiesData loads the entities data from the given package.
 *
 * It decodes it into an EntititesData struct
 */
func LoadEntitiesData(pkg resource.SurvivelerPackage) (*EntitiesData, error) {
	md := new(EntitiesData)
	err := pkg.LoadJSON(entitiesURI, &md)
	return md, err
}

func newGameData(pkg resource.SurvivelerPackage) (*gameData, error) {
	var (
		gd  *gameData
		err error
	)
	gd = new(gameData)
	gd.entitiesData = make(EntityDataDict)
	gd.buildingsData = make(BuildingDataDict)

	// load map data and information
	if gd.mapData, err = LoadMapData(pkg); err != nil {
		return nil, err
	}
	if gd.mapData.ScaleFactor == 0 {
		return nil, errors.New("'scale_factor' can't be 0")
	}
	// package must contain the path to world matrix bitmap
	fname, ok := gd.mapData.Resources["matrix"]
	if !ok {
		return nil, errors.New("'matrix' field not found in the map asset")
	}
	var worldBmp image.Image
	if worldBmp, err = pkg.LoadBitmap(fname); err == nil {
		if gd.world, err =
			game.NewWorld(worldBmp, gd.mapData.ScaleFactor); err != nil {
			return nil, err
		}
	}

	// TODO: this map is hard-coded for now, but will be read from resources
	// in the future
	_entityTypes["grunt"] = game.TankEntity
	_entityTypes["programmer"] = game.ProgrammerEntity
	_entityTypes["engineer"] = game.EngineerEntity
	_entityTypes["zombie"] = game.ZombieEntity
	_entityTypes["barricade"] = game.BarricadeBuilding
	_entityTypes["mg_turret"] = game.MgTurretBuilding

	// load entities URI map
	var (
		em *EntitiesData
		t  game.EntityType
	)
	if em, err = LoadEntitiesData(pkg); err != nil {
		return nil, err
	}
	for name, uri := range em.Entities {
		var entityData EntityData
		err = pkg.LoadJSON(uri, &entityData)
		if err != nil {
			return nil, err
		}
		if t, ok = _entityTypes[name]; !ok {
			return nil, fmt.Errorf("couldn't find type of '%s' entity", name)
		}
		log.WithFields(
			log.Fields{"name": name, "type": t, "data": entityData}).
			Debug("Loaded EntityData")
		gd.entitiesData[t] = &entityData
	}
	for name, uri := range em.Buildings {
		var buildingData BuildingData
		err = pkg.LoadJSON(uri, &buildingData)
		if err != nil {
			return nil, err
		}
		if t, ok = _entityTypes[name]; !ok {
			return nil, fmt.Errorf("couldn't find type of '%s' building", name)
		}
		log.WithFields(log.Fields{"name": name, "type": t, "data": buildingData}).
			Debug("Loaded BuildingData")
		gd.buildingsData[t] = &buildingData
	}
	// finally, validate world
	err = gd.validateWorld(gd.world)
	if err != nil {
		return nil, err
	}
	return gd, nil
}

/*
 * validateWorld performs some consistency and logical checks on the world
 */
func (gd *gameData) validateWorld(world *game.World) error {
	// validate player spawn point
	spawnPoints := gd.mapData.AIKeypoints.Spawn
	for i := range spawnPoints.Players {
		pt := world.TileFromWorldVec(spawnPoints.Players[i])
		if pt == nil {
			return fmt.Errorf(
				"player spawn point is out of bounds (%#v)",
				spawnPoints.Players[i])
		}
		if pt.Kind&game.KindWalkable == 0 {
			return fmt.Errorf(
				"player spawn point is located on a non-walkable point: (%#v)",
				*pt)
		}
	}

	// validate enemies spawn points
	if len(spawnPoints.Enemies) == 0 {
		return errors.New("at least one enemy spawn point must be defined")
	}
	for i := range spawnPoints.Enemies {
		zt := world.TileFromWorldVec(spawnPoints.Enemies[i])
		if zt == nil {
			return fmt.Errorf(
				"a Zombie spawn point is out of bounds: (%#v)",
				spawnPoints.Enemies[i])
		}
		if zt.Kind&game.KindWalkable == 0 {
			return fmt.Errorf(
				"a Zombie spawn point is located on a non-walkable tile: (%#v)",
				*zt)
		}
	}
	return nil
}
