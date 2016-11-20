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


def export_vertex(vertex: Vertex) -> str:
    """
    >>> export_vertex((2, -1, 3))
    'v 2.000000 -1.000000 3.000000'
    """
    return 'v ' + ' '.join(['{:.6f}'.format(p) for p in vertex])


def export_face_indices(face_indices: Iterable[int]) -> str:
    """
    Note: accepts indices and not vertices.

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


def export_mesh(mesh: List[Face]) -> str:
    """
    >>> v1 = (0.0, 0.0, 0.0)
    >>> v2 = (0.0, 0.0, 5.0)
    >>> v3 = (3.0, 0.0, 5.0)
    >>> v4 = (3.0, 0.0, 0.0)
    >>> v5 = (1.0, 1.0, 0.0)
    >>> v6 = (1.0, 1.0, 5.0)
    >>> mesh = [(v1, v2, v3, v4), (v3, v4, v5, v6)]
    >>> print(export_mesh(mesh))
    v 0.000000 0.000000 0.000000
    v 0.000000 0.000000 5.000000
    v 1.000000 1.000000 0.000000
    v 1.000000 1.000000 5.000000
    v 3.000000 0.000000 0.000000
    v 3.000000 0.000000 5.000000
    f 1 2 6 5
    f 6 5 3 4
    """
    ret = []
    vertices_indices = mesh2vertices(mesh)

    for vertex in sorted(vertices_indices.keys()):
        ret.append(export_vertex(vertex))

    for face in mesh:
        face_indices = tuple([vertices_indices[vertex] for vertex in face])
        ret.append(export_face_indices(face_indices))

    return '\n'.join(ret)


# NB: Commented out since doctests are executed by pytest (--doctest-modules)
# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
