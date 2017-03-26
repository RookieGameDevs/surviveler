from game.entities.entity import Entity
from game.entities.map_object import MapObject
from matlib.vec import Vec
from renderlib.material import Material
from renderlib.mesh import MeshProps
from renderlib.texture import Texture


class Map(Entity):
    """Map entity."""

    def __init__(self, resource, scene):
        """Constructor.

        :param resource: Resource containing map data.
        :type resource: :class:`resource_manager.Resource`

        :param scene: Scene to add the health bar to.
        :type scene: :class:`renderlib.scene.Scene`
        """
        super().__init__()

        mesh = resource['walls_mesh']
        texture = Texture.from_image(
            resource['walls_texture'],
            Texture.TextureType.texture_2d)

        material = Material()
        material.texture = texture
        material.receive_light = True

        props = MeshProps()
        props.material = material
        props.receive_shadows = False
        props.cast_shadows = False

        self.obj = scene.add_mesh(mesh, props)
        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        self.obj.position = Vec(0.0, 0.0, 1.0)

        self.objects = []

        # Initialize static objects
        for obj in resource.data['objects']:
            self.add_object(
                MapObject(resource[obj['ref']], scene, obj))

    def add_object(self, obj):
        """Add a static object to the map.

        :param obj: The object to be added
        :type obj: :class:`game.entitites.map_object.MapObject`
        """
        self.objects.append(obj)

    def update(self, dt):
        # NOTE: nothing to do
        pass

    def remove(self):
        for obj in self.objects:
            obj.remove()
        self.obj.remove()
