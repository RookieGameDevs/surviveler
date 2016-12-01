# -*- coding: utf-8 -*-
"""
Main module to create a Wavefront obj file from a png one.

Involved steps:
    1 - convert a png to a walkable matrix;
    2 - find wall perimeters -> list of 2D edges;
    3 - extrude vertically the wall perimeters -> list of 3D faces;
    4 - export faces to obj.

Python-3 only due to the type hinting (and 'super') syntax.

Glossary (to try to make some clearness):
    * box - an element in the walkable matrix, with coordinates (x, y)
    * block - a non-walkable box
    * vertex - a 2/3D point in a 2/3D space (used to describe wall perimeters and meshes)
    * wall perimeter - a 2D closed planar (z=0) polygon which corresponds to the wall borders
        (from a "top" view perspective).
        If the wall is open, you have 1 perimeter for 1 wall.
        If the wall is closed, you have an internal wall perimeter and an external one.
        Each png or level may consists of several separated walls.
"""
from extruder import extrude_wall_perimeters
from wavefront import export_mesh
from PIL import Image
from collections import deque
from collections import namedtuple
from collections import Counter
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

Pos = Tuple[int, int]
Vertex2D = Tuple[float, float]
Vector2D = Vertex2D
WallPerimeter = List[Vertex2D]
WalkableMatrix = List[List[int]]
VertexBoxes = NamedTuple('NearBoxes',
    [
        ('upleft', Pos),
        ('upright', Pos),
        ('downright', Pos),
        ('downleft', Pos),
    ]
)


Box = namedtuple('Box', ['x', 'y'])
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


# A vertex ha 4 neighbour boxes, and each box can be walkable or not (block).
# This map represents every case with relative "mouvement" possibility
# of a vertex to track the wall perimeter.

POSSIBLE_DIRECTIONS = {
    ((0, 0),
     (0, 0)): (),
    ((0, 0),
     (0, 1)): (RIGHT, DOWN),
    ((0, 0),
     (1, 0)): (LEFT, DOWN),
    ((0, 0),
     (1, 1)): (LEFT, RIGHT),
    ((0, 1),
     (0, 0)): (UP, RIGHT),
    ((0, 1),
     (0, 1)): (UP, DOWN),
    ((0, 1),
     (1, 0)): (LEFT, UP, RIGHT, DOWN),
    ((0, 1),
     (1, 1)): (LEFT, UP),
    ((1, 0),
     (0, 0)): (LEFT, UP),
    ((1, 0),
     (0, 1)): (LEFT, UP, RIGHT, DOWN),
    ((1, 0),
     (1, 0)): (UP, DOWN),
    ((1, 0),
     (1, 1)): (UP, RIGHT),
    ((1, 1),
     (0, 0)): (LEFT, RIGHT),
    ((1, 1),
     (0, 1)): (LEFT, DOWN),
    ((1, 1),
     (1, 0)): (RIGHT, DOWN),
    ((1, 1),
     (1, 1)): (),
}  # type: Dict[Tuple[Vector2D, Vector2D], Tuple[Vector2D, ...]]


RULES = {
    ((0, 0),
     (0, 0)): {STILL: STILL, UP: UP, LEFT: LEFT, RIGHT: RIGHT, DOWN: DOWN},  # XXX
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
     (1, 1)): {STILL: STILL, UP: STILL, DOWN: STILL, LEFT: STILL, RIGHT: STILL},  # XXX
}  # type: Dict[Tuple[Vector2D, Vector2D], Dict[Vector2D, Vector2D]]


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


class BlocksMap(dict):
    """
    Class to perform operation on a blocks map, a dict of non-walkable boxes
    (not exactly a walkable matrix).

    TODO: Use a walkable matrix instead, eventually.
    """
    def __init__(self, data: Mapping, map_size: Tuple[int, int], box_size: int=1) -> None:
        super().__init__(data)
        self.map = data
        self.map_size = map_size
        self.box_size = box_size

    def get_grid_vertices(self) -> Iterable[Vertex2D]:
        """Returns an iterator for all map virtual "grid" vertices,
        so regardless they are part of a wall or not.
        """
        width, height = self.map_size
        for bx in range(width):
            for by in range(height):
                x = bx * self.box_size
                y = by * self.box_size
                yield (x, y)

    def map_vertex(self, xy: Vertex2D) -> Pos:
        """Given a vertex position, returns the map box whose the
        vertex is the top-left one.
        """
        x, y = xy
        return int(x / self.box_size), int(y / self.box_size)

    def vertex2boxes(self, xy: Vertex2D) -> VertexBoxes:
        """Returns the 4 neighbour map boxes (white or not)
        which share the same given vertex.
        """
        bx, by = self.map_vertex(xy)
        return VertexBoxes(upleft=(bx - 1, by - 1), upright=(bx, by - 1), downleft=(bx - 1, by), downright=(bx, by))

    def boxes2block_matrix(self, boxes: VertexBoxes) -> Tuple[Pos, Pos]:
        """Given 4 vertex boxes, returns a 2x2 tuple with walkable/non-walkable info.
        """
        return ((self.map.get(boxes.upleft, 0), self.map.get(boxes.upright, 0)), (self.map.get(boxes.downleft, 0), self.map.get(boxes.downright, 0)))

    def build(self) -> List[List[Vertex2D]]:
        """Main method (edge detection): builds the list of wall perimeters.
        """
        ret = []  # type: List[WallPerimeter]

        print('\n{:,}'.format(len(self.map)))

        import turtle
        turtle.mode('logo')
        turtle.speed(9)
        drawsize = int(200 / (1 + max(map(max, self.map)))) if self.map else 0  # type: ignore

        if not self.map:
            return []

        tracked_vertices = Counter()  # type: Dict[Vertex2D, int]
        dbg_versor_names = []

        for iv, vertex in enumerate(self.get_grid_vertices()):
            v_boxes = self.vertex2boxes(vertex)
            blocks_matrix = self.boxes2block_matrix(v_boxes)
            versors = POSSIBLE_DIRECTIONS[blocks_matrix]
            n_versors = len(versors)
            if n_versors == 0:
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

            if len(self.map) < 200:
                # Don't draw with turtle
                turtle.penup()
                turtle.setpos(wall_vertex[0] * drawsize, -wall_vertex[1] * drawsize)
                turtle.pendown()

            while True:
                print('all tracked vertices =', tracked_vertices)
                print('current wall_perimeter =', wall_perimeter)
                print('went {} (versor = {}) to {}'.format(VERSOR_NAME[versor], versor, wall_vertex))
                print('=== Current vertex:', wall_vertex, '===')

                v_boxes = self.vertex2boxes(wall_vertex)
                blocks_matrix = self.boxes2block_matrix(v_boxes)
                versors = POSSIBLE_DIRECTIONS[blocks_matrix]
                tracked_vertices[wall_vertex] += (1 if len(versors) == 4 else 2)

                versor_next = RULES[blocks_matrix][versor]
                print('versor_next = {} ({})'.format(versor_next, VERSOR_NAME[versor_next]))
                v_next = sum_vectors(wall_vertex, versor_next)

                wall_perimeter.append(v_next)
                print('adding vertex', v_next)

                old_versor = versor
                versor = versor_next
                dbg_versor_names.append(VERSOR_NAME[versor])
                print('turns =', dbg_versor_names)
                wall_vertex = wall_perimeter[-1]

                if len(self.map) < 200:
                    turtle.setheading(ANGLES[versor_next])
                    turtle.fd(drawsize)

                if wall_vertex == first_vertex:
                    print('Starter vertex reached.')
                    break

            wall_perimeter = remove_internal_edge_points(wall_perimeter)
            wall_perimeter = normalized_perimeter(wall_perimeter)
            ret.append(wall_perimeter)

        ret.sort()
        return ret


def mat2map(matrix: WalkableMatrix) -> BlocksMap:
    """Creates a blocks map from a walkable matrix.
    """
    ret = {}
    for y, row in enumerate(matrix):
        for x, walkable in enumerate(row):
            if not walkable:
                ret[(x, y)] = 1
    return BlocksMap(ret, map_size=(x + 1, y + 1))


def load_png(filepath: str) -> WalkableMatrix:
    """Builds a walkable matrix from an image.
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
            row.append(int(walkable))
        ret.append(row)
    return ret


def png2obj(filepath: str, height: float=3) -> int:
    """Main function which takes an image filepath and creates
    a mesh (detecting edges an extruding them vertically)
    exporting it in a wavefront obj format.

    Returns the size, in byte, of the obj created.
    """
    print('Loading {}...'.format(filepath))
    t0 = time.time()
    matrix = load_png(filepath)
    print('{:.2f} s'.format(time.time() - t0))

    blocks_map = mat2map(matrix)
    print('Detecting edges...')
    t0 = time.time()
    wall_perimeters = sorted(blocks_map.build())
    print('{:.2f} s'.format(time.time() - t0))
    mesh = extrude_wall_perimeters(wall_perimeters, height)

    dst = filepath[:-4] + '.obj'
    print('Exporting mesh to Wavefront...')
    t0 = time.time()
    with open(dst, 'w') as fp:
        fp.write(export_mesh(mesh))
    print('{:.2f} s'.format(time.time() - t0))
    obj_size = os.path.getsize(dst)
    print('{} created ({:,} byte).'.format(dst, obj_size))
    return obj_size


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='png2obj: creates a 3D-level Wavefront obj from a png')
    parser.add_argument('src', help='the source png file path')
    parser.add_argument('--height', default=3.0, type=float,
                        help='vertical extrusion amount [default=%(default)s]')
    args = parser.parse_args()
    png2obj(args.src, args.height)
