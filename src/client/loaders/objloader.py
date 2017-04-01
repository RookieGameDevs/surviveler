"""
OBJ file loader.

Suitable to import 3d models exported from Blender.
"""
import logging


LOG = logging.getLogger(__name__)

KEYWORD_DESC = {
    'v': 'vertex',
    'vt': 'UV',
    'vn': 'normal',
    'f': 'face',
}


class OBJLoaderError(Exception):
    pass


class OBJFormatError(OBJLoaderError):
    pass


class OBJTypeError(OBJFormatError):
    pass


def load_obj(fp):
    """Loads `fp` and return a tuple of vertices, normals, uvs, indices
    lists.

    :param fp: The .obj file point.
    :type fp: File

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

    def do_nothing(lineno, keyword, data):
        """Handler for unused rows (comments, object names, etc - see samples)."""
        LOG.debug('Skipped line {}: {} {}'.format(
            lineno, keyword, ' '.join(data)))

    def parse_vector(lineno, keyword, data, xargs):
        kwd_desc = KEYWORD_DESC[keyword]
        if len(data) == xargs:
            try:
                return [float(component) for component in data]
            except ValueError:
                raise OBJTypeError(
                    'Line {lineno}: expected float values for {kwd_desc} data. '
                    'Got values: {data}'.format(**locals()))

        actual_length = len(data)
        raise OBJFormatError(
            'Line {lineno}: expected {xargs} arguments for {kwd_desc} data. '
            'Got: {actual_length}'.format(**locals()))

    def parse_vertex(lineno, keyword, data):
        tmp_vertices.append(parse_vector(lineno, keyword, data, 3))

    def parse_texture(lineno, keyword, data):
        tmp_uvs.append(parse_vector(lineno, keyword, data, 2))

    def parse_normal(lineno, keyword, data):
        tmp_normals.append(parse_vector(lineno, keyword, data, 3))

    def parse_face(lineno, keyword, data):
        if len(data) != 3:
            raise OBJFormatError(
                'Line {lineno}: only triangle faces are supported'.format(lineno))

        for face in data:
            try:
                # convert index values to integers and normalize them to 0 base,
                # set missing indices to -1
                face_items = [int(i) - 1 if i else -1 for i in face.split('/')]
                if not face_items:
                    raise ValueError('invalid face spec')

                # clamp items array to 3 elements
                if len(face_items) < 3:
                    face_items.append([-1] * (3 - len(face_items)))

            except (ValueError, TypeError) as err:
                LOG.warn('Failed to parse face {}: {}'.format(face, err))
                continue

            vert_idx = face_items[0]
            indices.append(len(indices))
            vertices.append(tmp_vertices[vert_idx])

            uv_idx = face_items[1]
            if uv_idx >= 0:
                uvs.append(tmp_uvs[uv_idx])

            norm_idx = face_items[2]
            if norm_idx >= 0:
                normals.append(tmp_normals[norm_idx])

    func_map = {
        'v': parse_vertex,
        'vt': parse_texture,
        'vn': parse_normal,
        'f': parse_face,
    }

    for lineno, line in enumerate(fp.splitlines()):
        data = line.split()
        try:
            keyword, values = data[0], data[1:]
        except IndexError:
            # skip empty lines
            continue
        func_map.get(keyword, do_nothing)(lineno, keyword, values)

    return vertices, normals, uvs, indices
