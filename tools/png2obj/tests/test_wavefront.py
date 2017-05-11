from png2obj.wavefront import create_wavefront
from png2obj.wavefront import export_mesh
from png2obj.wavefront import mesh2vertices


def test_mesh2vertices():    
    v1 = (0.0, 0.0, 0.0)  # 1
    v2 = (0.0, 0.0, 5.0)  # 2
    v3 = (3.0, 0.0, 5.0)  # 6
    v4 = (3.0, 0.0, 0.0)  # 5
    v5 = (1.0, 1.0, 0.0)  # 3
    v6 = (1.0, 1.0, 5.0)  # 4
    mesh = [(v1, v2, v3, v4), (v3, v4, v5, v6)]
    vertices = mesh2vertices(mesh)
    assert set(vertices) == set([v1, v2, v3, v4, v5, v6])

    # Checks vertex ordering.
    assert vertices[v1] == 1
    assert vertices[v2] == 2
    assert vertices[v5] == 3
    assert vertices[v6] == 4
    assert vertices[v4] == 5
    assert vertices[v3] == 6


def test_export_mesh():
    # TODO: refactor this ugly form.
    v1 = (0.0, 0.0, 0.0)
    v2 = (0.0, 0.0, 5.0)
    v3 = (3.0, 0.0, 5.0)
    v4 = (3.0, 0.0, 0.0)
    v5 = (1.0, 1.0, 0.0)
    v6 = (1.0, 1.0, 5.0)

    expected = """
v 0.000000 0.000000 0.000000
v 0.000000 0.000000 5.000000
v 1.000000 1.000000 0.000000
v 1.000000 1.000000 5.000000
v 3.000000 0.000000 0.000000
v 3.000000 0.000000 5.000000
f 1 2 6 5
f 6 5 3 4
""".strip()
    mesh = [(v1, v2, v3, v4), (v3, v4, v5, v6)]
    assert export_mesh(mesh, readable_export_settings=('+x', '+y', '+z')) == expected
    
    expected = """
v 0.000000 -0.000000 0.000000
v 0.000000 -5.000000 0.000000
v 1.000000 -0.000000 1.000000
v 1.000000 -5.000000 1.000000
v 3.000000 -0.000000 0.000000
v 3.000000 -5.000000 0.000000
f 1 2 6 5
f 6 5 3 4
""".strip()
    assert export_mesh(mesh, readable_export_settings=('+x', '-z', '+y')) == expected


def test_create_wavefront():
    vertices = [(0, 0, 0), (2, 0, 0), (2, 1, 0), (2, 0, 1)]
    faces = [(0, 1, 2), (0, 1, 3)]
    expected = """
v 0.000000 0.000000 0.000000
v 2.000000 0.000000 0.000000
v 2.000000 0.000000 1.000000
v 2.000000 1.000000 0.000000
f 1 2 3
f 1 2 4
""".strip()
    actual = create_wavefront(vertices=vertices, faces=faces, zero_index=True, dst='mesh.obj')
    assert actual == expected
