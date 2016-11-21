"""
Main module to create a Wavefront obj file from a png one.

Python-3 only due to the type hinting (and 'super') syntax.

Glossary:
    * box - an element in the walkable matrix, with coordinates (x, y)
    * block - a non-walkable box
    * vertex - a 2/3D point in a 2/3D space
    * wall perimeter - a closed polygon which corresponds to a wall border.
        If the wall is open, you have 1 perimeter for 1 wall.
        If the wall is closed, you have an internal wall perimeter and an external one.
"""
from extruder import extrude_wall_perimeters
from wavefront import export_mesh
from PIL import Image
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
import os
import sys
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
VERSOR_NAME = {
    LEFT: 'left', UP: 'up', RIGHT: 'right', DOWN: 'down', HERE: 'here'
}  # type: Dict[Vector2D, str]


# A vertex ha 4 neighbour boxes, and each box can be walkable or not (block).
# This map represents every case with relative "mouvement" possibility
# of a vertex to track the wall perimeter.
POSSIBLE_DIRECTIONS = {
    ((0, 0),
     (0, 0)): (HERE, HERE),
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
     (1, 1)): (HERE, HERE),
}  # type: Dict[Tuple[Vector2D, Vector2D], Tuple[Vector2D, ...]]


def sum_vectors(v1: Vector2D, v2: Vector2D) -> Vector2D:
    """Sums 2 bi-dimensional vectors.

    >>> v1 = (-1, 2)
    >>> v2 = (3.0, -10)
    >>> sum_vectors(v1, v2)
    (2.0, -8)
    """
    return (v1[0] + v2[0], v1[1] + v2[1])


def scalar(vector: Vector2D, amount: float) -> Vector2D:
    """Multiplies a vector by a scalar.
    """
    return vector[0] * amount, vector[1] * amount


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


def normalized_perimeter(wall_perimeter: WallPerimeter) -> WallPerimeter:
    """
    Normalizes the wall perimeter to make it start from its topleft.

    >>> normalized_perimeter([(1, 0), (1, 1), (0, 1), (0, 0), (1, 0)])
    [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    """
    minimum = min(wall_perimeter)
    # Remove duplicates preserving order:
    wall_perimeter = list(OrderedDict.fromkeys(wall_perimeter))
    deq = deque(wall_perimeter)  # use deque just to use the rotate (circular shift)
    while deq[0] != minimum:
        deq.rotate(1)
    # The last item must be equal to the first by convention.
    deq.append(deq[0])
    return list(deq)


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
        for by in range(height):
            for bx in range(width):
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

    def get_next_block_vertices(self, vertex: Vertex2D) -> List[Vertex2D]:
        """Returns neighbour vertices which are actually block edges or vertices
        (i.e. contiguous to map walls, so not free space vertices).
        """
        ret = []  # type: List[Vertex2D]
        v_boxes = self.vertex2boxes(vertex)
        versors = POSSIBLE_DIRECTIONS[self.boxes2block_matrix(v_boxes)]
        ret = [sum_vectors(vertex, v) for v in versors]
        return ret

    def vertex2blocks(self, xy: Vertex2D) -> List[Pos]:
        """Given a vertex, returns the non-walkable neighbour boxes.
        """
        return [box for box in self.vertex2boxes(xy) if box in self.map]

    def is_border_vertex(self, vertex: Vertex2D) -> bool:
        """Returns True if the vertex is part of an edge or is a corner.
        Returns false if the vertex is inner a wall or outside.
        """
        v_blocks = self.vertex2blocks(vertex)
        return 0 < len(v_blocks) < 4

    def build(self) -> List[List[Vertex2D]]:
        """Main method (edge detection): builds the list of wall perimeters.
        """
        ret = []  # type: List[WallPerimeter]
        tracked_vertices = set()  # type: Set[Vertex2D]
        if not self.map:
            return []

        for iv, vertex in enumerate(self.get_grid_vertices()):
            if not self.is_border_vertex(vertex):
                continue

            if vertex in tracked_vertices:
                continue

            # start new wall perimeter from this disjointed block
            wall_perimeter = []

            first_vertex = vertex
            old_versor = (0.0, 0.0)  # like a `None` but supporting the array sum
            wall_perimeter.append(vertex)
            closable = False
            wall_vertex = vertex
            while True:
                tracked_vertices.add(wall_vertex)

                vertices = self.get_next_block_vertices(wall_vertex)
                # Cycle through new possible vertices to explore
                for v_next in vertices:
                    versor_next = sum_vectors(v_next, scalar(wall_perimeter[-1], -1))

                    # Avoid to go back
                    if sum_vectors(old_versor, versor_next) == (0.0, 0.0):
                        continue

                    if v_next not in tracked_vertices:
                        wall_perimeter.append(v_next)
                        break
                    else:
                        if v_next == wall_perimeter[0]:
                            # could close the polygon
                            closable = True

                if v_next in tracked_vertices:
                    if closable:
                        wall_perimeter.append(first_vertex)
                    break

                versor = sum_vectors(v_next, scalar(wall_perimeter[-1], -1))

                wall_vertex = v_next
                old_versor = versor

            wall_perimeter = remove_internal_edge_points(wall_perimeter)
            wall_perimeter = normalized_perimeter(wall_perimeter)
            ret.append(wall_perimeter)

        ret.sort()
        return ret


def mat2map(matrix: Iterable[Iterable[int]]) -> BlocksMap:
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
    matrix = load_png(filepath)
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
    print('Done.')
    return os.path.getsize(dst)


def main(*args: str) -> None:
    src = args[0]
    height = 3.0
    if len(args) == 2:
        height = float(args[1])
    print(png2obj(src, height))


if __name__ == '__main__':
    main(*sys.argv[1:])
