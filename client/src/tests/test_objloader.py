from loaders import load_obj
import numpy as np
import pytest


@pytest.mark.parametrize("obj_filename,n_vertices_and_normals,indices", [
    ('triangle.obj', 3, (1, 0, 2)),
    ('square.obj', 6, (0, 3, 2, 0, 1, 3)),  # 3 * 2 triangles
    ('pyramid.obj', 12, (0, 1, 2, 2, 1, 3, 3, 1, 0, 0, 2, 3)),
])
def test_n_vertices_and_normals(obj_filename,
        n_vertices_and_normals, indices):
    vertices, normals, uvs, actual_indices = load_obj(
        'src/tests/samples/models/{}'.format(obj_filename))

    assert len(vertices) == len(normals) == n_vertices_and_normals * 3
    # Works with both lists and numpy.array objects
    assert np.all(actual_indices == np.array(indices, dtype=np.int32))
