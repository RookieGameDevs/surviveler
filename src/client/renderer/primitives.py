from renderlib.mesh import Mesh


class Rect(Mesh):
    def __init__(self, width, height):
        vertices = [
            (0, 0, 0),
            (0, -height, 0),
            (width, -height, 0),
            (width, 0, 0),
        ]
        normals = [
            (0, 0, 1),
            (0, 0, 1),
            (0, 0, 1),
            (0, 0, 1),
        ]
        indices = [
            0, 1, 2,
            2, 3, 0
        ]
        uvs = [
            (0, 1),
            (0, 0),
            (1, 0),
            (1, 1),
        ]
        super().__init__(vertices, indices, normals, uvs)
