/*
 * Surviveler package
 * game data: loading from assets
 */
package surviveler

import (
	"errors"
	"fmt"
	"image"
	"io"
	"path"
	"server/resource"

	"golang.org/x/image/bmp"

	log "github.com/Sirupsen/logrus"
)

// URI of some static elements contained in a package
const (
	mapURI      string = "map/data.json"
	entitiesURI string = "entities/data.json"
)

// TODO: this map is hard-coded for now, but will be read from resources
// in the future
var _entityTypes = map[string]EntityType{}

func newGameData(pkg resource.Package) (*gameData, error) {
	var (
		gd  *gameData
		err error
	)
	gd = new(gameData)
	gd.entitiesData = make(EntityDataDict)
	gd.buildingsData = make(BuildingDataDict)
	gd.mapData = new(MapData)

	// load map data and information
	if err = resource.LoadJSON(pkg, mapURI, &gd.mapData); err != nil {
		return nil, err
	}
	// package must contain the path to wall+floors mesh
	fname, ok := gd.mapData.Resources["walls+floor_mesh"]
	if !ok {
		return nil, errors.New("'walls+floor' field not found in the map asset")
	}

	meshURI := path.Join("map", fname)
	if exists, rtype := pkg.Exists(meshURI); !exists || rtype != resource.File {
		return nil, fmt.Errorf("mesh at uri %v, no such file", meshURI)
	}

	// read and decode the bitmap from the package
	var (
		worldBmp image.Image
		item     resource.Item
		f        io.ReadCloser
	)
	item, err = pkg.Open(fname)
	if err != nil {
		return nil, err
	}
	f, err = item.Open()
	defer f.Close()
	if worldBmp, err = bmp.Decode(f); err == nil {
		if gd.world, err =
			NewWorld(worldBmp, gd.mapData.ScaleFactor); err != nil {
			return nil, err
		}
	}

	// TODO: this map is hard-coded for now, but will be read from resources
	// in the future
	_entityTypes["grunt"] = TankEntity
	_entityTypes["programmer"] = ProgrammerEntity
	_entityTypes["engineer"] = EngineerEntity
	_entityTypes["zombie"] = ZombieEntity
	_entityTypes["barricade"] = BarricadeBuilding
	_entityTypes["mg_turret"] = MgTurretBuilding

	// load entities URI map
	var (
		em *EntitiesData
		t  EntityType
	)
	em = new(EntitiesData)
	if err = resource.LoadJSON(pkg, entitiesURI, &em); err != nil {
		return nil, fmt.Errorf("couldn't decode EntitiesData from %v: %v", entitiesURI, err)
	}
	for name, uri := range em.Entities {
		uri = path.Join(uri, "data.json")
		entityData := new(EntityData)
		err = resource.LoadJSON(pkg, uri, &entityData)
		if err != nil {
			return nil, fmt.Errorf("couldn't decode EntityData from %v: %v", uri, err)
		}
		if t, ok = _entityTypes[name]; !ok {
			return nil, fmt.Errorf("couldn't find type of '%s' entity", name)
		}
		log.WithFields(
			log.Fields{"name": name, "type": t, "data": entityData}).
			Debug("Loaded EntityData")
		gd.entitiesData[t] = entityData
	}
	for name, uri := range em.Buildings {
		var buildingData BuildingData
		uri = path.Join(uri, "data.json")
		err = resource.LoadJSON(pkg, uri, &buildingData)
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
func (gd *gameData) validateWorld(world *World) error {
	// validate player spawn point
	spawnPoints := gd.mapData.AIKeypoints.Spawn
	for i := range spawnPoints.Players {
		pt := world.TileFromWorldVec(spawnPoints.Players[i])
		if pt == nil {
			return fmt.Errorf(
				"player spawn point is out of bounds (%#v)",
				spawnPoints.Players[i])
		}
		if pt.Kind&KindWalkable == 0 {
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
		if zt.Kind&KindWalkable == 0 {
			return fmt.Errorf(
				"a Zombie spawn point is located on a non-walkable tile: (%#v)",
				*zt)
		}
	}
	return nil
}
