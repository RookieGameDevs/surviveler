from game.entities.entity import Entity
from renderlib.material import Material
from renderlib.mesh import MeshProps
from renderlib.texture import Texture


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, resource, scene):
        """Constructor.

        :param resource: The terrain resource
        :type resource: :class:`loaders.Resource`

        :param scene: Scene to add the terrain to.
        :type scene: :class:`renderlib.scene.Scene`
        """
        super().__init__()

        mesh = resource['floor_mesh']
        texture = Texture.from_image(resource['floor_texture'], Texture.TextureType.texture_2d)

        material = Material()
        material.texture = texture

        props = MeshProps()
        props.material = material
        props.receive_shadows = True
        props.cast_shadows = False

        self.obj = scene.add_mesh(mesh, props)
        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        # self.obj.position.z = 1.0

    def update(self, dt):
        # NOTE: nothing to do here
        pass

    def remove(self):
        self.obj.remove()
