"""
OBJ file loader.

Suitable to import 3d models exported from Blender.
"""


def load_obj(filename):
    """
    Loads `filename` and return a tuple of vertices, normals, uvs, indices lists.

    :param filename: The .obj file to load.
    :type filename: str

    :returns: The mesh vertices, normals, UVs and vertex indices parsed from the .obj file.
    :rtype: tuple
    """
    # TODO: Support compressed files

    tmp_vertices = []
    tmp_normals = []
    tmp_uvs = []

    vertices = []
    normals = []
    uvs = []

    # vertex indices
    indices = []

    with open(filename, 'r') as f:
        for line in f:
            header, *data = line.split()

            if header == 'v':
                tmp_vertices.append([float(x) for x in data])

            if header == 'vt':
                tmp_uvs.append([float(x) for x in data])

            if header == 'vn':
                tmp_normals.append([float(x) for x in data])

            if header == 'f':

                for face in data:
                    face_items = face.split('/')
                    idx0 = int(face_items[0]) - 1
                    indices.append(idx0)
                    try:
                        idx1 = int(face_items[1]) - 1
                    except ValueError:
                        pass
                    else:
                        uvs += tmp_uvs[idx1]
                    idx2 = int(face_items[2]) - 1
                    vertices += tmp_vertices[idx0]
                    normals += tmp_normals[idx2]

    return vertices, normals, uvs, indices
