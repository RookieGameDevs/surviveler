/*
 * Surviveler game package
 * game data
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

type (
	buildingDataType map[game.EntityType]*resource.BuildingData
	entityDataType   map[game.EntityType]*resource.EntityData
)

type gameData struct {
	mapData      *resource.MapData
	buildingData buildingDataType
	entityData   entityDataType
}

func (gd *gameData) load(pkg resource.SurvivelerPackage) (world *game.World, err error) {
	gd.entityData = make(entityDataType)
	gd.buildingData = make(buildingDataType)

	// load map data and information
	if gd.mapData, err = pkg.LoadMapData(); err != nil {
		return
	}
	if gd.mapData.ScaleFactor == 0 {
		err = errors.New("'scale_factor' can't be 0")
	}
	// package must contain the path to world matrix bitmap
	if fname, ok := gd.mapData.Resources["matrix"]; !ok {
		err = errors.New("'matrix' field not found in the map asset")
	} else {
		var worldBmp image.Image
		if worldBmp, err = pkg.LoadBitmap(fname); err == nil {
			if world, err =
				game.NewWorld(worldBmp, gd.mapData.ScaleFactor); err == nil {
			}
		}
	}
	if err != nil {
		return
	}

	// load entities URI map
	var (
		em *resource.EntitiesData
		t  game.EntityType
		ok bool
	)
	if em, err = pkg.LoadEntitiesData(); err != nil {
		return
	}
	for name, uri := range em.Entities {
		var entityData resource.EntityData
		if pkg.LoadJSON(uri, &entityData); err != nil {
			return
		} else {
			if t, ok = _entityTypes[name]; !ok {
				err = fmt.Errorf("Couldn't find type of '%s' entity", name)
				return
			}
			log.WithFields(
				log.Fields{"name": name, "type": t, "data": entityData}).
				Debug("Loaded EntityData")
			gd.entityData[t] = &entityData
		}
	}
	for name, uri := range em.Buildings {
		var buildingData resource.BuildingData
		if pkg.LoadJSON(uri, &buildingData); err != nil {
			return
		} else {
			if t, ok = _entityTypes[name]; !ok {
				err = fmt.Errorf("Couldn't find type of '%s' building", name)
				return
			}
			log.WithFields(log.Fields{"name": name, "type": t, "data": buildingData}).
				Debug("Loaded BuildingData")
			gd.buildingData[t] = &buildingData
		}
	}
	// finally, validate worl
	err = gd.validateWorld(world)
	return
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
