# -*- coding: utf-8 -*-
"""
Main module to create a Wavefront obj file from a png one.
Find perimeter/edges and extrude walls vertically.

Involved steps:
    1 - convert a png to a walkability matrix;
    2 - find wall perimeters -> list of 2D edges;
    3 - extrude vertically the wall perimeters -> list of 3D faces;
    4 - export faces to obj.

Python-3 only due to the type hinting (and 'super') syntax.

Glossary (to try to make some clearness):
    * cell - an element in the walkability matrix, with coordinates (x, y)
    * block - a non-walkable cell
    * vertex - a 2/3D point in a 2/3D space (used to describe wall perimeters and meshes)
    * wall perimeter - a 2D closed planar (z=0) polygon which corresponds to the wall borders
        (from a "top" view perspective).
        If the wall is open, you have 1 perimeter for 1 wall.
        If the wall is closed, you have an internal wall perimeter and an external one.
        Each png or level may consists of several separated walls.
"""
from collections import Counter
from collections import OrderedDict
from collections import deque
from collections import namedtuple
from typing import Dict  # noqa
from typing import Iterable
from typing import List
from typing import Mapping
from typing import NamedTuple
from typing import Set  # noqa
from typing import Tuple
import argparse
import os
import time
import turtle as logo

# 3rd parties
from PIL import Image

# Own modules
from extruder import extrude_wall_perimeters
from wavefront import export_mesh


Pos = Tuple[int, int]
Versor2D = Tuple[int, int]
Vertex2D = Tuple[float, float]
Vector2D = Vertex2D
Vertex3D = Tuple[float, float, float]
WallPerimeter = List[Vertex2D]
WalkabilityMatrix = List[List[int]]
VertexCells = NamedTuple('NearCells',
    [
        ('upleft', Pos),
        ('upright', Pos),
        ('downright', Pos),
        ('downleft', Pos),
    ]
)


Cell = namedtuple('Cell', ['x', 'y'])
NearVertices = namedtuple('NearVertices', ['left', 'up', 'right', 'down'])


LEFT = (-1, 0)
UP = (0, -1)
RIGHT = (1, 0)
DOWN = (0, 1)
HERE = (0, 0)
STILL = (0, 0)
VERSOR_NAME = {
    LEFT: 'left', UP: 'up', RIGHT: 'right', DOWN: 'down', HERE: 'here'
}  # type: Dict[Vector2D, str]

# Angles for the turtle
ANGLES = {LEFT: 270, UP: 0, RIGHT: 90, DOWN: 180}  # type: Dict[Vertex2D, int]


# A vertex ha 4 neighbour cells, and each cell can be walkable or not (block).
# This map represents every case with relative "mouvement" possibility
# of a vertex to track the wall perimeter.

RULES = {
    ((0, 0),
     (0, 0)): {},
    ((0, 0),
     (0, 1)): {STILL: RIGHT, UP: RIGHT, LEFT: DOWN},
    ((0, 0),
     (1, 0)): {STILL: DOWN, UP: LEFT, RIGHT: DOWN},
    ((0, 0),
     (1, 1)): {STILL: RIGHT, RIGHT: RIGHT, LEFT: LEFT},
    ((0, 1),
     (0, 0)): {STILL: UP, LEFT: UP, DOWN: RIGHT},
    ((0, 1),
     (0, 1)): {STILL: UP, UP: UP, DOWN: DOWN},
    ((0, 1),
     (1, 0)): {STILL: RIGHT, UP: RIGHT, LEFT: DOWN, RIGHT: UP, DOWN: LEFT},
    ((0, 1),
     (1, 1)): {STILL: UP, RIGHT: UP, DOWN: LEFT},
    ((1, 0),
     (0, 0)): {STILL: LEFT, RIGHT: UP, DOWN: LEFT},
    ((1, 0),
     (0, 1)): {STILL: RIGHT, UP: LEFT, DOWN: RIGHT, LEFT: UP, RIGHT: DOWN},
    ((1, 0),
     (1, 0)): {STILL: UP, UP: UP, DOWN: DOWN},
    ((1, 0),
     (1, 1)): {STILL: RIGHT, LEFT: UP, DOWN: RIGHT},
    ((1, 1),
     (0, 0)): {STILL: RIGHT, LEFT: LEFT, RIGHT: RIGHT},
    ((1, 1),
     (0, 1)): {STILL: LEFT, UP: LEFT, RIGHT: DOWN},
    ((1, 1),
     (1, 0)): {STILL: RIGHT, UP: RIGHT, LEFT: DOWN},
    ((1, 1),
     (1, 1)): {},
}  # type: Dict[Tuple[Vector2D, Vector2D], Dict[Versor2D, Versor2D]]


DRAW_SIZE = 300


def sum_vectors(v1: Vector2D, v2: Vector2D) -> Vector2D:
    """Sums 2 bi-dimensional vectors.

    >>> v1 = (-1, 2)
    >>> v2 = (3.0, -10)
    >>> sum_vectors(v1, v2)
    (2.0, -8)
    """
    return (v1[0] + v2[0], v1[1] + v2[1])


def remove_internal_edge_points(vertices: List[Vertex2D]) -> List[Vertex2D]:
    """
    Leaves only the points that are in the corners.

    >>> points = [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 3), (-2, 3), (-3, 3)]
    >>> remove_internal_edge_points(points)
    [(0, 0), (0, 3), (-3, 3)]
    """
    ret = [vertices[0]]
    for i in range(1, len(vertices) - 1):
        # Make the diff of 3 current contiguous vertices
        dx1 = vertices[i][0] - vertices[i - 1][0]
        dy1 = vertices[i][1] - vertices[i - 1][1]
        dx2 = vertices[i + 1][0] - vertices[i][0]
        dy2 = vertices[i + 1][1] - vertices[i][1]
        # If the 2 diffs are not equal:
        if (dx1 != dx2) or (dy1 != dy2):
            # the 3 vertices don't form a line, so get the median one
            ret.append(vertices[i])

    ret.append(vertices[-1])
    return ret


def remove_contiguous_values(lst: List[Tuple[float, float]]) -> None:
    """
    Removes *in place* multiple values if they are contiguous.

    :param lst: the list of 2D points.

    >>> lst = [1, 2, 8, 8, 8, 0, 0, 5]
    >>> remove_contiguous_values(lst)
    >>> lst
    [1, 2, 8, 0, 5]
    """
    i = 0
    while i < len(lst) - 1:
        if lst[i] == lst[i + 1]:
            del lst[i]
        else:
            i += 1


def normalized_perimeter(wall_perimeter: WallPerimeter) -> WallPerimeter:
    """
    Normalizes the wall perimeter to make it start from its topleft.

    >>> normalized_perimeter([(1, 0), (1, 1), (0, 1), (0, 0), (1, 0)])
    [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    """
    minimum = min(wall_perimeter)
    deq = deque(wall_perimeter)  # use deque just to use the rotate (circular shift)
    while deq[0] != minimum:
        deq.rotate(1)
    # The last item must be equal to the first by convention.
    deq.append(deq[0])
    ret = list(deq)
    # Remove contiguous duplicates, preserving order.
    remove_contiguous_values(ret)
    return ret


def list_to_index_map(the_list: list) -> OrderedDict:
    """Basically convert a list into a dictionary.
    """
    ret = OrderedDict()
    assert len(set(the_list)) == len(the_list), 'Error: the list contains duplicated elements'
    for i, element in enumerate(the_list):
        ret[element] = i
    return ret


def wall_perimeters_to_verts_edges(wall_perimeters: List[WallPerimeter]) -> Tuple[List[Vertex2D], List[Tuple[int, int]]]:
    """
    Return a (a, b) tuple in which:
    * a -- unique vertices
    * b -- list of vertex indices couples

    >>> verts, edges = wall_perimeters_to_verts_edges([[(0, 0), (3, 0), (3, 1), (0, 1), (0, 0)], [(3, 1), (4, 1), (4, 2), (3, 2), (3, 1)]])
    >>> len(verts)
    7
    >>> verts.count((3, 1))
    1
    >>> verts
    [(0, 0), (3, 0), (3, 1), (0, 1), (4, 1), (4, 2), (3, 2)]
    >>> edges
    [(0, 1), (1, 2), (2, 3), (3, 0), (2, 4), (4, 5), (5, 6), (6, 2)]
    """
    # TODO: speed-up with dict for vertex indices
    verts = []
    edges = []

    for wall in wall_perimeters:
        for vertex in wall:
            if vertex not in verts:
                verts.append(vertex)

    for wall in wall_perimeters:
        for i in range(0, len(wall) - 1):
            vertex_i = wall[i]
            vertex_i1 = wall[i + 1]
            edges.append((verts.index(vertex_i), verts.index(vertex_i1)))

    return verts, edges


def build_walls(walls_map: Mapping, map_size: Tuple[int, int], cell_size: int=1, turtle=False) -> List[List[Vertex2D]]:
    """
    Main function (edge detection): builds the list of wall perimeters.

    TODO: Use a walkability matrix instead of walls_map.
    """

    def get_grid_vertices() -> Iterable[Vertex2D]:
        """Returns an iterator for all map virtual "grid" vertices,
        so regardless they are part of a wall or not.
        """
        width, height = map_size
        for bx in range(width):
            for by in range(height):
                x = bx * cell_size
                y = by * cell_size
                yield (x, y)

    def map_vertex(xy: Vertex2D) -> Pos:
        """Given a vertex position, returns the map cell whose the
        vertex is the top-left one.
        """
        x, y = xy
        return int(x / cell_size), int(y / cell_size)

    def vertex2cells(xy: Vertex2D) -> VertexCells:
        """Returns the 4 neighbour map cells (white or not)
        which share the same given vertex.
        """
        bx, by = map_vertex(xy)
        return VertexCells(upleft=(bx - 1, by - 1), upright=(bx, by - 1), downleft=(bx - 1, by), downright=(bx, by))

    def cells2block_matrix(cells: VertexCells) -> Tuple[Pos, Pos]:
        """Given 4 vertex cells, returns a 2x2 tuple with walkable/non-walkable info.
        """
        return ((walls_map.get(cells.upleft, 0), walls_map.get(cells.upright, 0)), (walls_map.get(cells.downleft, 0), walls_map.get(cells.downright, 0)))

    ret = []  # type: List[WallPerimeter]

    if turtle:
        logo.mode('logo')
        logo.speed(11)
        drawsize = int(DRAW_SIZE / (1 + max(map(max, walls_map)))) if walls_map else 0  # type: ignore

    if not walls_map:
        return []

    tracked_vertices = Counter()  # type: Dict[Vertex2D, int]

    for iv, vertex in enumerate(get_grid_vertices()):
        v_cells = vertex2cells(vertex)
        blocks_matrix = cells2block_matrix(v_cells)
        versors = RULES[blocks_matrix]
        n_versors = len(versors) - 1  # remove still
        if n_versors == -1:
            # not a border verdex
            # inside 4 blocks or 4 empty cells
            continue

        n_passes = tracked_vertices[vertex]
        if n_versors == 4:
            # should pass by here exactly 2 times
            if n_passes > 1:
                continue

        elif n_passes > 0:
            continue

        # start new wall perimeter from this disjointed block
        wall_perimeter = []

        first_vertex = vertex
        old_versor = (0, 0)  # like a `None` but supporting the array sum
        versor = old_versor
        wall_perimeter.append(vertex)
        wall_vertex = vertex

        if turtle:
            logo.penup()
            logo.setpos(wall_vertex[0] * drawsize - drawsize, -wall_vertex[1] * drawsize + drawsize)
            logo.pendown()

        while True:
            v_cells = vertex2cells(wall_vertex)
            blocks_matrix = cells2block_matrix(v_cells)
            versors = RULES[blocks_matrix]

            # Trick to handle the "chessboard" case.
            tracked_vertices[wall_vertex] += (1 if len(versors) == 5 else 2)

            versor_next = versors[versor]
            v_next = sum_vectors(wall_vertex, versor_next)
            wall_perimeter.append(v_next)

            old_versor = versor
            versor = versor_next
            wall_vertex = wall_perimeter[-1]

            if turtle:
                logo.setheading(ANGLES[versor_next])
                logo.fd(drawsize)

            if wall_vertex == first_vertex:
                break

        wall_perimeter = remove_internal_edge_points(wall_perimeter)
        wall_perimeter = normalized_perimeter(wall_perimeter)
        ret.append(wall_perimeter)

    ret.sort()
    return ret


def mat2map(matrix: WalkabilityMatrix) -> Mapping:
    """Creates a blocks map from a walkability matrix.
    """
    ret = {}
    for y, row in enumerate(matrix):
        for x, walkable in enumerate(row):
            if not walkable:
                ret[(x, y)] = 1
    return ret, (x + 1, y + 1)


def load_png(filepath: str) -> WalkabilityMatrix:
    """Builds a walkability matrix from an image.
    """
    ret = []
    img = Image.open(filepath)
    for y in range(img.height):
        row = []
        for x in range(img.width):
            pixel = img.getpixel((x, y))
            if img.mode == 'P':
                walkable = int(pixel > 0)
            else:
                if img.mode == 'RGBA':
                    alpha = pixel[3]
                    walkable = alpha == 0 or pixel[:3] == (255, 255, 255)
                else:
                    walkable = pixel[:3] == (255, 255, 255)

                # special reddish marker (temporary)
                if pixel[0] > pixel[1] and pixel[0] > pixel[2]:
                    print('reddish in', x, y)
                    walkable = -1
            row.append(int(walkable))
        ret.append(row)
    return ret


def matrix2obj(matrix, dst, height=1, turtle=False):
    """
    Given a walkability matrix return an obj.

    :param matrix: the walkability matrix.
    :type matrix: list.
    """
    blocks_map, map_size = mat2map(matrix)
    print('Detecting edges...')
    t0 = time.time()
    wall_perimeters = sorted(build_walls(blocks_map, map_size=map_size, turtle=turtle))
    print('{:.2f} s'.format(time.time() - t0))

    mesh = extrude_wall_perimeters(wall_perimeters, height)

    print('Exporting mesh to Wavefront...')
    t0 = time.time()
    with open(dst, 'w') as fp:
        fp.write(export_mesh(mesh))
    print('{:.2f} s'.format(time.time() - t0))
    obj_size = os.path.getsize(dst)
    print('{} created ({:,} byte).'.format(dst, obj_size))
    return obj_size


def png2obj(filepath: str, height: float=3, turtle: bool=False) -> int:
    """Main function which takes an image filepath and creates
    a mesh (detecting edges an extruding them vertically)
    exporting it in a wavefront obj format.

    Returns the size, in byte, of the obj created.
    """
    print('Loading {}...'.format(filepath))
    t0 = time.time()
    matrix = load_png(filepath)
    print('{:.2f} s'.format(time.time() - t0))

    dst = filepath[:-4] + '.obj'
    return matrix2obj(matrix, dst, height, turtle=turtle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='png2obj: creates a 3D-level Wavefront obj from a png')
    parser.add_argument('src', help='the source png file path')
    parser.add_argument('--height', default=3.0, type=float,
                        help='vertical extrusion amount [default=%(default)s]')
    parser.add_argument('--turtle', type=bool, default=False, help='show steps graphically for debugging')
    args = parser.parse_args()
    png2obj(args.src, args.height, turtle=args.turtle)
