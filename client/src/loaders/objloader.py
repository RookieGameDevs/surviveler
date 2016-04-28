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

    with open(filename) as f:
        for i, line in enumerate(f):
            items = line.split()
            if line.startswith('v '):
                v0 = float(items[1])
                v1 = float(items[2])
                v2 = float(items[3])
                tmp_vertices.append((v0, v1, v2))

            if line.startswith('vt '):
                uv0 = float(items[1])
                uv1 = float(items[2])
                tmp_uvs.append((uv0, uv1))

            if line.startswith('vn '):
                n0 = float(items[1])
                n1 = float(items[2])
                n2 = float(items[3])
                tmp_normals.append((n0, n1, n2))

            if line.startswith('f '):
                f0 = items[1]
                f1 = items[2]
                f2 = items[3]

                f0_items = f0.split('/')
                idx0 = int(f0_items[0]) - 1
                indices.append(idx0)
                try:
                    idx1 = int(f0_items[1]) - 1
                except ValueError:
                    pass
                else:
                    uvs += tmp_uvs[idx1]
                idx2 = int(f0_items[2]) - 1
                vertices += tmp_vertices[idx0]
                normals += tmp_normals[idx2]

                f1_items = f1.split('/')
                idx0 = int(f1_items[0]) - 1
                indices.append(idx0)
                try:
                    idx1 = int(f1_items[1]) - 1
                except ValueError:
                    pass
                else:
                    uvs += tmp_uvs[idx1]
                idx2 = int(f1_items[2]) - 1
                vertices += tmp_vertices[idx0]
                normals += tmp_normals[idx2]

                f2_items = f2.split('/')
                idx0 = int(f2_items[0]) - 1
                indices.append(idx0)
                try:
                    idx1 = int(f2_items[1]) - 1
                except ValueError:
                    pass
                else:
                    uvs += tmp_uvs[idx1]
                idx2 = int(f2_items[2]) - 1
                vertices += tmp_vertices[idx0]
                normals += tmp_normals[idx2]

    return vertices, normals, uvs, indices
