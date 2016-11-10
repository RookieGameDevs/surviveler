from typing import Tuple
import doctest

Vertex = Tuple[float, float, float]
Edge = Tuple[Vertex, Vertex]
Face = Tuple[Vertex, Vertex, Vertex, Vertex]


def extrude_edge(edge: Edge, h: float) -> Face:
    """
    Return the 4 vertices of the face with results from
    extrusion.

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
    fp1 = p1
    fp2 = p2
    fp3 = fp2[0], fp2[1], h
    fp4 = fp1[0], fp1[1], h
    return fp1, fp2, fp3, fp4


# NB: Commented out since doctests are executed by pytest (--doctest-modules)
# if __name__ == '__main__':
#     doctest.testmod()
