from game.components import Renderable
from game.entities.entity import Entity
from game.entities.map_object import MapObject
from matlib import Vec
from renderer.texture import Texture


class Map(Entity):
    """Map entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: Resource containing map data.
        :type resource: :class:`resource_manager.Resource`

        :param parent_node: Node to attach the map to.
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        shader = resource['shader']
        mesh = resource['walls_mesh']
        texture = Texture.from_image(resource['walls_texture'])
        # shader params
        params = {
            'tex': texture,
        }
        renderable = Renderable(
            parent_node,
            mesh,
            shader,
            params,
            textures=[texture],
            enable_light=True)

        super().__init__(renderable)

        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        self[Renderable].transform.translate(Vec(0.0, 0.0, 1.0))

        self.objects = []

        # Initialize static objects
        for obj in resource.data['objects']:
            self.add_object(
                MapObject(resource[obj['ref']], obj, self[Renderable].node))

    def add_object(self, obj):
        """Add a static object to the map.

        :param obj: The object to be added
        :type obj: :class:`game.entitites.map_object.MapObject`
        """
        self.objects.append(obj)

    def update(self, dt):
        # NOTE: nothing to do
        pass
