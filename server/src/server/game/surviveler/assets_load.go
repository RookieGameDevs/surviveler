/*
 * Surviveler game package
 * game data: loading from assets
 */
package surviveler

import (
	"errors"
	"fmt"
	log "github.com/Sirupsen/logrus"
	"image"
	"server/game"
	"server/game/resource"
)

// URI of some static elements contained in a package
const (
	mapURI      string = "map/data.json"
	entitiesURI string = "entities/data.json"
)

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

type gameData struct {
	world         *game.World
	mapData       *MapData
	buildingsData BuildingDataDict
	entitiesData  EntityDataDict
}

func (gd *gameData) newGameData(pkg resource.SurvivelerPackage) error {
	gd.entitiesData = make(EntityDataDict)
	gd.buildingsData = make(BuildingDataDict)

	// load map data and information
	var err error
	if gd.mapData, err = LoadMapData(pkg); err != nil {
		return err
	}
	if gd.mapData.ScaleFactor == 0 {
		return errors.New("'scale_factor' can't be 0")
	}
	// package must contain the path to world matrix bitmap
	fname, ok := gd.mapData.Resources["matrix"]
	if !ok {
		return errors.New("'matrix' field not found in the map asset")
	}
	var worldBmp image.Image
	if worldBmp, err = pkg.LoadBitmap(fname); err == nil {
		if gd.world, err =
			game.NewWorld(worldBmp, gd.mapData.ScaleFactor); err != nil {
			return err
		}
	}

	// load entities URI map
	var (
		em *EntitiesData
		t  game.EntityType
	)
	if em, err = LoadEntitiesData(pkg); err != nil {
		return err
	}
	for name, uri := range em.Entities {
		var entityData EntityData
		err = pkg.LoadJSON(uri, &entityData)
		if err != nil {
			return err
		}
		if t, ok = _entityTypes[name]; !ok {
			return fmt.Errorf("Couldn't find type of '%s' entity", name)
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
			return err
		}
		if t, ok = _entityTypes[name]; !ok {
			return fmt.Errorf("Couldn't find type of '%s' building", name)
		}
		log.WithFields(log.Fields{"name": name, "type": t, "data": buildingData}).
			Debug("Loaded BuildingData")
		gd.buildingsData[t] = &buildingData
	}
	// finally, validate world
	return gd.validateWorld(gd.world)
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
				"Player spawn point is out of bounds (%#v)",
				spawnPoints.Players[i])
		}
		if pt.Kind&game.KindWalkable == 0 {
			return fmt.Errorf(
				"Player spawn point is located on a non-walkable point: (%#v)",
				*pt)
		}
	}

	// validate enemies spawn points
	if len(spawnPoints.Enemies) == 0 {
		return errors.New("At least one enemy spawn point must be defined")
	}
	for i := range spawnPoints.Enemies {
		zt := world.TileFromWorldVec(spawnPoints.Enemies[i])
		if zt == nil {
			return fmt.Errorf(
				"A Zombie spawn point is out of bounds: (%#v)",
				spawnPoints.Enemies[i])
		}
		if zt.Kind&game.KindWalkable == 0 {
			return fmt.Errorf(
				"A Zombie spawn point is located on a non-walkable tile: (%#v)",
				*zt)
		}
	}
	return nil
}
