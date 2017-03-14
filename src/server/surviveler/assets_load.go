/*
 * Surviveler package
 * game data: loading from assets
 */
package surviveler

import (
	"errors"
	"fmt"
	"path"
	"server/resource"

	log "github.com/Sirupsen/logrus"
	"github.com/aurelien-rainone/go-detour/detour"
	"github.com/aurelien-rainone/gogeo/f32/d3"
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
	gd.world, err = NewWorld(pkg, gd.mapData)
	if err != nil {
		return nil, fmt.Errorf("can't create world, %s", err)
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
		ok bool
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
	var (
		st detour.Status
		q  *detour.NavMeshQuery
		f  detour.QueryFilter = detour.NewStandardQueryFilter()
	)
	if st, q = detour.NewNavMeshQuery(world.NavMesh, 2048); detour.StatusFailed(st) {
		return st
	}

	// validate player spawn point
	spawnPoints := gd.mapData.AIKeypoints.Spawn
	for i := range spawnPoints.Players {
		fmt.Println("validating player spawn point", i, "=", spawnPoints.Players[i])
		sp := d3.Vec3{spawnPoints.Players[i][0], 0, spawnPoints.Players[i][1]}
		ext := d3.Vec3{1, 1, 1}
		if st, ref, _ := q.FindNearestPoly(sp, ext, f); detour.StatusFailed(st) || !world.NavMesh.IsValidPolyRef(ref) {

			return fmt.Errorf(
				"invalid player spawn point (%#v), st(=%v), ref(%v)",
				spawnPoints.Players[i], st, ref)
		}
	}

	// validate enemies spawn points
	if len(spawnPoints.Enemies) == 0 {
		return errors.New("at least one enemy spawn point must be defined")
	}
	for i := range spawnPoints.Enemies {
		sp := d3.Vec3{spawnPoints.Enemies[i][0], 0, spawnPoints.Enemies[i][1]}
		ext := d3.Vec3{0, 1, 0}
		if st, ref, _ := q.FindNearestPoly(sp, ext, f); detour.StatusFailed(st) || !world.NavMesh.IsValidPolyRef(ref) {
			return fmt.Errorf(
				"invalid zombie spawn point (%#v)",
				spawnPoints.Enemies[i])
		}
	}
	return nil
}
