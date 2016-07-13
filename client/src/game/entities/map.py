from game.components import Renderable
from game.entities.entity import Entity
from math import pi
from matlib import Vec
from renderer import Texture
from utils import to_scene


Y_AXIS = Vec(0, 1, 0)


class MapObject(Entity):
    """Static object on the map."""

    def __init__(self, resource, parameters, parent_node):
        """Constructor.

        :param resource: Resource containing the object data.
        :type resource: :class:`resource_manager.Resource`

        :param parameters: Parameters for the object.
        :type parameters: :class:`dict`

        :param parent_node: Node to attach the object to.
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        mesh = resource['model']
        shader = resource['shader']
        texture = Texture.from_image(resource['texture'])

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

        self[Renderable].transform.translate(
            to_scene(*parameters['pos']))

        if 'rotation' in parameters:
            self[Renderable].transform.rotate(
                Y_AXIS, parameters['rotation'] * pi / 180)

    def update(self, dt):
        # NOTE: nothing to do
        pass


class Map(Entity):
    """Map entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: Resource containing map data.
        :type resource: :class:`resource_manager.Resource`

        :param parent_node: Node to attach the map to.
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        mesh = resource['mesh']
        shader = resource['walls_shader']

        params = {
            'color_ambient': Vec(0.4, 0.4, 0.4, 1),
            'color_diffuse': Vec(0.8, 0.8, 0.8, 1),
            'color_specular': Vec(1, 1, 1, 1),
        }
        renderable = Renderable(
            parent_node,
            mesh,
            shader,
            params,
            enable_light=True)

        super().__init__(renderable)

        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        self[Renderable].transform.translate(Vec(0.0, 0.0, 1.0))

        self.objects = []

        # Initialize static objects
        for obj in resource.data['objects']:
            self.objects.append(
                MapObject(resource[obj['ref']], obj, self[Renderable].node))

    def update(self, dt):
        # NOTE: nothing to do
        pass
