from context import Context
from game.components import Renderable
from game.entities.entity import Entity
from matlib.vec import Vec
from renderlib.core import Material
from renderlib.core import MeshRenderProps
from renderlib.texture import Texture


class Terrain(Entity):
    """Terrain entity."""

    def __init__(self, resource, parent_node):
        """Constructor.

        :param resource: The terrain resource
        :type resource: :class:`loaders.Resource`

        :param parent_node: Parent node to attach the terrain entity to.
        :type param_node: subclass of :class:`renderer.SceneNode`
        """
        mesh = resource['floor_mesh']
        texture = Texture.from_image(
            resource['floor_texture'],
            Texture.TextureType.texture_2d)

        material = Material()
        material.texture = texture

        props = MeshRenderProps()
        props.material = material
        props.receive_shadows = True
        props.cast_shadows = False
        props.light = Context.get_instance().light

        renderable = Renderable(parent_node, mesh, props)

        super().__init__(renderable)

        # FIXME: this offset here is due to the calculation of the walkable
        # matrix that adds one more walkable line on top of the scenario.
        self[Renderable].transform.translatev(Vec(0.0, 0.0, 1.0))

    def update(self, dt):
        # NOTE: nothing to do here
        pass
