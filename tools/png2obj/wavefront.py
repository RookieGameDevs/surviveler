# -*- coding: utf-8 -*-
"""
Module that handles the actual exporting in Wavefront .obj format.
"""
from collections import OrderedDict
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple

Vertex = Tuple[float, float, float]
Edge = Tuple[Vertex, Vertex]
Face = Tuple[Vertex, Vertex, Vertex, Vertex]
Mesh = List[Face]
ExportSettings = Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]

AXES = 'xyz'  # http://forum.wordreference.com/threads/axis-vs-axes.82527/
RIGHT, FORWARD, UP = 0, 1, 2
DEFAULT_EXPORT_SETTINGS = ('+x', '-z', '+y')


def parse_readable_export_settings(
        export_settings: Tuple[str, str, str]) -> ExportSettings:
    """
    See the doctest below:

    >>> parse_readable_export_settings(('+x', '-z', '+y'))
    ((0, 1), (2, -1), (1, 1))
    """
    ret = []  # type: List[Tuple[int, int]]
    sign_dic = {'-': -1, '+': 1}
    for s in export_settings:
        sign, axis = sign_dic[s[0]], AXES.index(s[1])
        ret.append((axis, sign))
    return ret[0], ret[1], ret[2]  # just to help mypy with returned tuple length


def export_vertex(
        vertex: Vertex, export_settings: ExportSettings) -> str:
    """
    Builds the Wavefront row of a vertex.

    >>> export_vertex((-7, 3, 5), export_settings=((0, 1), (1, 1), (2, 1)))
    'v -7.000000 3.000000 5.000000'
    >>> export_vertex((2, -1, 3), export_settings=((0, 1), (2, -1), (1, 1)))  # +x, -z, +y
    'v 2.000000 -3.000000 -1.000000'
    """
    # Tuple index must be an integer literal = mypy seems not support integer variables as indces for tuple
    right = vertex[export_settings[RIGHT][0]] * export_settings[RIGHT][1]  # type: ignore
    forward = vertex[export_settings[FORWARD][0]] * export_settings[FORWARD][1]  # type: ignore
    up = vertex[export_settings[UP][0]] * export_settings[UP][1]  # type: ignore
    return 'v ' + ' '.join(['{:.6f}'.format(component) for component in (right, forward, up)])


def export_face_indices(face_indices: Iterable[int]) -> str:
    """Returns the Wavefront row representation of a face.

    NB: accepts indices and NOT vertices coordinates.

    >>> export_face_indices((1, 5, 6, 2))
    'f 1 5 6 2'
    """
    return 'f ' + ' '.join([str(vertex_index) for vertex_index in face_indices])


def mesh2vertices(mesh: Mesh) -> Dict[Vertex, int]:
    """
    Extracts unique vertices from mesh faces.

    >>> v1 = (0.0, 0.0, 0.0)  # 1
    >>> v2 = (0.0, 0.0, 5.0)  # 2
    >>> v3 = (3.0, 0.0, 5.0)  # 6
    >>> v4 = (3.0, 0.0, 0.0)  # 5
    >>> v5 = (1.0, 1.0, 0.0)  # 3
    >>> v6 = (1.0, 1.0, 5.0)  # 4
    >>> mesh = [(v1, v2, v3, v4), (v3, v4, v5, v6)]
    >>> vertices = mesh2vertices(mesh)
    >>> set(vertices) == set([v1, v2, v3, v4, v5, v6])
    True

    Checks vertex ordering.

    >>> vertices[v1]
    1
    >>> vertices[v2]
    2
    >>> vertices[v5]
    3
    >>> vertices[v6]
    4
    >>> vertices[v4]
    5
    >>> vertices[v3]
    6
    """
    ret = OrderedDict()  # type: Dict[Vertex, int]

    unique = set()
    for face in mesh:
        for vertex in face:
            unique.add(vertex)

    for i, vertex in enumerate(sorted(list(unique)), 1):
        ret[vertex] = i

    return ret


def export_mesh(
        mesh: List[Face],
        readable_export_settings: Tuple[str, str, str]=DEFAULT_EXPORT_SETTINGS) -> str:
    """
    Returns a Wavefront representation of a mesh (list of faces).

    >>> v1 = (0.0, 0.0, 0.0)
    >>> v2 = (0.0, 0.0, 5.0)
    >>> v3 = (3.0, 0.0, 5.0)
    >>> v4 = (3.0, 0.0, 0.0)
    >>> v5 = (1.0, 1.0, 0.0)
    >>> v6 = (1.0, 1.0, 5.0)
    >>> mesh = [(v1, v2, v3, v4), (v3, v4, v5, v6)]
    >>> print(export_mesh(mesh, readable_export_settings=('+x', '+y', '+z')))
    v 0.000000 0.000000 0.000000
    v 0.000000 0.000000 5.000000
    v 1.000000 1.000000 0.000000
    v 1.000000 1.000000 5.000000
    v 3.000000 0.000000 0.000000
    v 3.000000 0.000000 5.000000
    f 1 2 6 5
    f 6 5 3 4
    >>> print(export_mesh(mesh, readable_export_settings=('+x', '-z', '+y')))
    v 0.000000 -0.000000 0.000000
    v 0.000000 -5.000000 0.000000
    v 1.000000 -0.000000 1.000000
    v 1.000000 -5.000000 1.000000
    v 3.000000 -0.000000 0.000000
    v 3.000000 -5.000000 0.000000
    f 1 2 6 5
    f 6 5 3 4
    """
    ret = []

    export_settings = parse_readable_export_settings(readable_export_settings)

    vertices_indices = mesh2vertices(mesh)
    for vertex in sorted(vertices_indices.keys()):
        ret.append(export_vertex(vertex, export_settings))

    for face in mesh:
        face_indices = tuple([vertices_indices[vertex] for vertex in face])
        ret.append(export_face_indices(face_indices))

    return '\n'.join(ret)
