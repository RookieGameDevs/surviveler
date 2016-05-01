"""
OBJ file loader.

Suitable to import 3d models exported from Blender.
"""


def load_obj(filename):
    """Loads `filename` and return a tuple of vertices, normals, uvs, indices
    lists.

    :param filename: The .obj file to load.
    :type filename: str

    :returns: The mesh vertices, normals, UVs and vertex indices parsed from the
        .obj file.
    :rtype: tuple
    """

    tmp_vertices = []
    tmp_normals = []
    tmp_uvs = []

    vertices = []
    normals = []
    uvs = []

    # vertex indices
    indices = []

    def do_nothing(arg):
        pass

    def parse_vector(data):
        return [float(component) for component in data]

    def parse_vertex(data):
        tmp_vertices.append(parse_vector(data))

    def parse_texture(data):
        tmp_uvs.append(parse_vector(data))

    def parse_normal(data):
        tmp_normals.append(parse_vector(data))

    def parse_face(data):
        for face in data:
            face_items = face.split('/')
            idx0 = int(face_items[0]) - 1
            indices.append(idx0)
            try:
                idx1 = int(face_items[1]) - 1
            except ValueError:
                pass
            else:
                uvs.append(tmp_uvs[idx1])
            idx2 = int(face_items[2]) - 1
            vertices.extend(tmp_vertices[idx0])
            normals.extend(tmp_normals[idx2])

    func_map = {
        'v': parse_vertex,
        'vt': parse_texture,
        'vn': parse_normal,
        'f': parse_face,
    }

    with open(filename, 'r') as f:
        for line in f:
            data = line.split()
            try:
                header, values = data[0], data[1:]
            except IndexError:
                continue
            func_map.get(header, do_nothing)(values)

    return vertices, normals, uvs, indices
