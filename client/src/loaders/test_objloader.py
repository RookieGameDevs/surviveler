from objloader import load_obj
import pytest

@pytest.mark.parametrize("obj_filename,n_vertices_and_normals", [
    ('triangle.obj', 3),
    ('square.obj', 6),  # 3 * 2 triangles
])
def test_n_vertices_and_normals(obj_filename, n_vertices_and_normals):
    vertices, normals, uvs = load_obj('tests/samples/3dmodels/{}'.format(obj_filename))
    assert len(vertices) == len(normals) == n_vertices_and_normals * 3
