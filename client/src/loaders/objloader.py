"""
OBJ file loader.

Suitable to import 3d models exported from Blender.
"""
import logging


LOG = logging.getLogger(__name__)


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
            try:
                # convert index values to integers and normalize them to 0 base,
                # set missing indices to -1
                face_items = [int(i) - 1 if i else -1 for i in face.split('/')]
                if not face_items:
                    raise ValueError('invalid face spec')

                # clamp items array to 3 elements
                if len(face_items) < 3:
                    face_items.extend([-1] * (3 - len(face_items)))

            except (ValueError, TypeError) as err:
                LOG.warn('Failed to parse face {}:'.format(face, err))
                continue

            vert_idx = face_items[0]
            indices.append(vert_idx)
            vertices.extend(tmp_vertices[vert_idx])

            uv_idx = face_items[1]
            if uv_idx >= 0:
                uvs.append(tmp_uvs[uv_idx])

            norm_idx = face_items[2]
            if norm_idx >= 0:
                normals.extend(tmp_normals[norm_idx])

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
