# -*- coding: utf-8 -*-
"""
Utility funcion for extrusion.
"""
from typing import List
from typing import Tuple
from typing import Union

Vertex2 = Tuple[float, float]
Vertex3 = Tuple[float, float, float]
Vertex = Union[Vertex2, Vertex3]
Edge = Tuple[Vertex, Vertex]  # no 3D required here
Face = Tuple[Vertex3, Vertex3, Vertex3, Vertex3]  # 3D here
Mesh = List[Face]
WallPerimeter = List[Vertex]


def path2edges(path: List[Vertex]) -> List[Edge]:
    """
    Converts a list of vertices in a list of edges. (trivial)

    >>> vertices = [(0.0, 1.0), (1.0, 1.0), (1.0, -1.0)]
    >>> len(vertices)
    3
    >>> edges = path2edges(vertices)
    >>> len(edges)
    2
    >>> len(edges[0])
    2
    >>> len(edges[1])
    2
    >>> edges
    [((0.0, 1.0), (1.0, 1.0)), ((1.0, 1.0), (1.0, -1.0))]
    """
    ret = []
    for i in range(len(path) - 1):
        edge = path[i], path[i + 1]
        ret.append(edge)
    return ret


def extrude_edge(edge: Edge, amount: float) -> Face:
    """
    Returns the 4 vertices of the face which results from
    vertical extrusion of an edge.
    The face triangulation is delegated to Blender.

    :param edge: the edge to extrude.
    :param amount: how much to extrude along the Z-axis.

    >>> p1 = 1.0, 2.0, 0.0
    >>> p2 = 3.0, 2.0, 0.0
    >>> h = 3.0
    >>> face = extrude_edge((p1, p2), h)
    >>> fp1, fp2, fp3, fp4 = face
    >>> fp1
    (1.0, 2.0, 0.0)
    >>> fp2
    (3.0, 2.0, 0.0)
    >>> fp3
    (3.0, 2.0, 3.0)
    >>> fp4
    (1.0, 2.0, 3.0)
    """
    p1, p2 = edge
    # If is a 2D edge set 3rd dimension to 0
    fp1 = p1[0], p1[1], p1[2] if len(p1) == 3 else 0.0
    fp2 = p2[0], p2[1], p2[2] if len(p2) == 3 else 0.0
    fp3 = fp2[0], fp2[1], fp2[2] + amount
    fp4 = fp1[0], fp1[1], fp1[2] + amount
    return fp1, fp2, fp3, fp4


def extrude_path(path: List[Vertex], amount: float) -> Mesh:
    """Returns a mesh by extruding vertically the given list of points.
    """
    return [extrude_edge(edge, amount) for edge in path2edges(path)]


def extrude_wall_perimeters(wall_perimeters: List[WallPerimeter], amount: float) -> Mesh:
    """Utility which gets the output of the edge detector (the list of wall perimeters)
    and returns the resulting mesh, obtained by extrusion.
    """
    mesh = []
    for wall in wall_perimeters:
        mesh.extend(extrude_path(wall, amount))
    return mesh
