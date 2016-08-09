from renderer.scene import SceneNode
from matlib import Vec

#: Maximum number of sources
MAX_LIGHT_SOURCES = 1

#: Light sources data
LIGHT_SOURCES = {}


class Light:
    """Light source."""

    def __init__(self, color=None):
        self.color = color or Vec(1, 1, 1, 1)
        self.shininess = 60.0


class LightNode(SceneNode):
    """Light source node."""

    #: Mapping of available light sources
    LIGHT_IDS = {i: True for i in range(MAX_LIGHT_SOURCES)}

    def __init__(self, light):
        super(LightNode, self).__init__()

        self.light_id = LightNode.gen_id()
        self.light = light

    def __del__(self):
        LightNode.LIGHT_IDS[self.light_id] = True
        LIGHT_SOURCES.pop(self.light_dir, None)

    @classmethod
    def gen_id(cls):
        try:
            light_id = [i for i in range(MAX_LIGHT_SOURCES) if cls.LIGHT_IDS[i]][0]
            cls.LIGHT_IDS[light_id] = False
            return light_id
        except IndexError:
            raise RuntimeError('Maximum number of lights reached')

    def render(self, ctx, transform):
        LIGHT_SOURCES[self.light_id] = {
            'color': self.light.color,
            'position': Vec(transform[0, 3], transform[1, 3], transform[2, 3]),
            'shininess': self.light.shininess,
        }
